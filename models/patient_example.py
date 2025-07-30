from fhir.resources.patient import Patient
from pydantic import BaseModel, field_validator, model_validator, ValidationError, StringConstraints, Field, ConfigDict
from typing import Annotated, List
from datetime import datetime
from fhir.resources.R4B.fhirtypes import DateType
from enum import Enum

# this class defines an enum we'll use in the model below
class PatientGenderEnum(str, Enum):
    male = 'Male'
    female = 'Female'
    other = 'Other'
    unknown = 'Unknown'

# mini-model for diagnoses we'll use below
class DiagnosisModel(BaseModel):
    code: str | None = Field(
        default=None,
        title='DiagnosisCode',
        description='Code for the diagnosis'
    )
    description: str | None = Field(
        default=None,
        title='Diagnosis Description',
        description='Description of the diagnosis'
    )
    diagnosis_date: datetime | None = Field(
        default=None,
        title='DiagnosisDate',
        description='Date of the diagnosis'
    )

    # now let's set a useful validation on this model: either the 'code' or the 'description' must be populated
    @model_validator(mode='after')
    def enforce_population_of_code_or_description(self):
        if not any([self.code, self.description]):
            raise ValidationError('Record must contain either a code or a description')
        return self

# and now for the main patient model
class ExamplePatientModel(BaseModel):
    # required field uses StringConstraints to enforce minimum length and strip whitespace if needed
    # (note, you can also set the attribute 'str_strip_whitespace=True' using the model_config settings to do the whitespace bit,
    # but then it will apply to all str fields in the model, which may not be exactly what you want)
    mrn: Annotated[str, StringConstraints(min_length=5, strip_whitespace=True)] = Field(
        title='PatientIdentifier',
        description='Unique Identifier for the patient'
    )
    # optional field using StringConstraints to convert to uppercase.
    # Note pipe-delim'ed typing allowing for possibility that field is not passed at all in raw data
    # If field does not exist in raw data, it will exist in the created object, defaulted to None
    last_diagnosed_ckd_stage: Annotated[str, StringConstraints(to_upper=True)] | None = Field(
        default=None,
        title='LastCKDStage',
        description='Last diagnosed CKD Stage of the patient'
    )
    # some fields using standard pythonic primitive types
    ccd_enrolled: bool = Field(
        default=False,
        title='CKDEnrollmentStatus',
        description='Current enrollment status of the patient'
    )
    patient_age: int = Field(
        title='PatientAge',
        description='Age of the patient'
    )
    last_encounter_date: datetime | None = Field(
        default=None,
        title='LastEncounterDate',
        description="Date of the patient's last encounter"
    )
    # example field constrained to an enum
    # (this isn't generally a good idea for a model into which you're placing raw data, unless you intend to have
    # a mapping step prior to placing raw data into the model. See below for a simple example for how to do this)
    patient_gender: PatientGenderEnum = Field(
        default=PatientGenderEnum.unknown,
        title='PatientGender',
        description='Gender of the patient'
    )
    # example of a list type
    patient_first_name: List[Annotated[str, StringConstraints(strip_whitespace=True)]] = Field(
        title='PatientFirstNameList',
        description='List of patient first names'
    )
    # this field uses the FHIR 'Date' type, which is more flexible and better constrained than the datetime.date type
    patient_date_of_birth: DateType = Field(
        title='PatientDateOfBirth',
        description='Date of birth of the patient'
    )
    # use our diagnosis mini-model above in a list for this field
    comorbid_diagnoses: List[DiagnosisModel] | None = Field(
        default=None,
        title='ComorbidDiagnoses',
        description='List of comorbid diagnoses'
    )

    model_config = ConfigDict(use_enum_values=True, revalidate_instances='always', validate_assignment=True)

# some demonstrations and tests
if __name__ == '__main__':

    # simple function to map raw incoming values to our gender Enum
    def simple_gender_mapper(raw_gender: str):
        raw_values_to_enum = {
            'M': PatientGenderEnum.male,
            'Ma': PatientGenderEnum.male,
            'F': PatientGenderEnum.female,
            'Fem': PatientGenderEnum.female,
            'U': PatientGenderEnum.unknown,
            'O': PatientGenderEnum.other,
            'Oth': PatientGenderEnum.other
        }
        mapped_value = raw_values_to_enum[raw_gender]
        return mapped_value

    # a sample incoming patient record
    sample_raw_patient = {
            'mrn': '12345',
            'last_diagnosed_ckd_stage': 'ckd3a',
            'ccd_enrolled': True,
            'patient_age': 45,
            'last_encounter_date': '2025-04-30',
            'patient_gender': 'M',
            'patient_first_name': 'Tommy',
            'patient_date_of_birth': '1980-03-31',
            'hypertension_diagnosis': 'I10^Chronic_Hypertension',
            'diabetes_diagnosis': 'E85^Diabetes Melitus'
        }

    # couple of those fields need some simple transforms applied it into our model, which we can do inline
    # transform the gender into a value from the Enum
    sample_raw_patient['patient_gender'] = simple_gender_mapper(sample_raw_patient['patient_gender'])
    # make the patient's name a list, as required
    sample_raw_patient['patient_first_name'] = [sample_raw_patient['patient_first_name']]
    # take those diagnosis fields and create DiagnosisModel objects from them, put them into a list and in the correct field
    sample_raw_patient['comorbid_diagnoses'] = [
        DiagnosisModel.model_validate({
            'code': sample_raw_patient['hypertension_diagnosis'].split('^')[0],
            'description': sample_raw_patient['hypertension_diagnosis'].split('^')[1]
        }),
        DiagnosisModel.model_validate({
            'code': sample_raw_patient['diabetes_diagnosis'].split('^')[0],
            'description': sample_raw_patient['diabetes_diagnosis'].split('^')[1]
        })
    ]
    # the model doesn't forbid extra fields, so we don't need to remove the hypertension_diagnosis and diabetes_diagnosis fields from our sample dict
    # so now let's validate our incoming data against the model, and create an ExamplePatientModel object
    validated_patient = ExamplePatientModel.model_validate(sample_raw_patient)

    # easily go back to a dict, if you want:
    validated_patient_dict = validated_patient.model_dump()
    print(f'Patient object as dict:\n{validated_patient_dict}\n')

    # need JSON?
    validated_patient_json = validated_patient.model_dump_json(indent=2,exclude_none=True)
    print(f'Patient object as JSON:\n{validated_patient_json}')


