import unittest
from parsers.hl7_to_dict import HL7MessageToDict
import json

class TestHL7MessageToDict(unittest.TestCase):
    def test_parse_hl7_message(self):
        msh1 = "MSH|^~\\&|MESA_RPT_MGR|EAST_RADIOLOGY|iFW|XYZ|||ORU^R01|MESA3b|P|2.4||||||||"
        pid1 = "PID|||CR3^^^ADT1||CRTHREE^PAUL|||M|||2222 HOME STREET^^ANN ARBOR^MI^^USA||555-555-2004~444-333-222|||M"
        pv11 = "PV1||1|CE||||12345^SMITH^BARON^H|||||||||||"
        obr1 = "OBR|||||||20010501141500.0000||||||||||||||||||F||||||||||||||||||"
        obx11 = "OBX|1|HD|SR Instance UID||1.113654.1.2001.30.2.1||||||F||||||"
        obx21 = "OBX|2|TX|SR Text||Radiology Report History Cough Findings PA evaluation of the chest demonstrates the lungs to be expanded and clear.  Conclusions Normal PA chest x-ray.||||||F||||||"
        cti1 = "CTI|study1|^1|^10_EP1"

        hl7_message_string1 = f'{msh1}\n{pid1}\n{pv11}\n{obr1}\n{obx11}\n{obx21}\n{cti1}'

        msh2 = "MSH|^~\\&|GHH_ADT||||20080115153000||ADT^A01^ADT_A01|0123456789|P|2.5||||AL"
        evn2 = "EVN||20080115153000||AAA|AAA|20080114003000"
        pid2 = "PID|1||566-554-3423^^^GHH^MR||EVERYMAN^ADAM^A|||M|||2222 HOME STREET^^ANN ARBOR^MI^^USA||555-555-2004~444-333-222|||M"
        nk12 = "NK1|1|NUCLEAR^NELDA^W|SPO|2222 HOME STREET^^ANN ARBOR^MI^^USA"
        pv12 = "PV1|1|I|GHH PATIENT WARD|U||||^SENDER^SAM^^MD|^PUMP^PATRICK^P|CAR||||2|A0|||||||||||||||||||||||||||||2008"
        in12 = "IN1|1|HCID-GL^GLOBAL|HCID-23432|HC PAYOR, INC.|5555 INSURERS CIRCLE^^ANN ARBOR^MI^99999^USA||||||||||||||||||||||||||||||||||||||||||||444-33-3333"

        hl7_message_string2 = f'{msh2}\n{evn2}\n{pid2}\n{nk12}\n{pv12}\n{in12}'

        parsed_first_message = HL7MessageToDict(hl7_message_string1).parse_hl7_message()
        parsed_second_message = HL7MessageToDict(hl7_message_string2).parse_hl7_message()

        self.assertEqual(parsed_first_message['PV1'].get('PV1-7-2'), 'SMITH')
        self.assertEqual(parsed_second_message['PID'].get('PID-5-1'), 'EVERYMAN')