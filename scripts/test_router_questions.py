from pathlib import Path
import sys
import json

repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.domain_intent_model import DomainIntentRouter, parse_training_csv, train_router, result_to_dict

QUESTIONS = [
"ntk550dd vs ntk550de",
"List down all the compatible components for 130-5144-900",
"Compare 130-5144-900 with 130-4476-940",
"Compare 130-5144-900 transceiver pec with 130-4476-940 transceiver pec",
"How do CFP2-DCO modules differ from QSFP-DD modules in terms of functionality and design?",
"list all the transceiver that support 6500-D/S platform",
"list down all the components added newly in the latest version for 130-5144-900",
"What are the types of sub-network connections (SNCs) supported by 6500 Packet-Optical Platform?",
"who are the primary/secondary approver for 130-5144-900",
"What is the latest version for 130-5144-900",
"fetch transceiver for an attribute with condition (e.g., list down all the transceiver where Extinction ratio is greater than 6 dB)",
"How are MPO connector lane assignments managed in 160-9607-900 400GBASE-SR8 module?",
"show all customers and their associated PEC codes",
"What is the approval status for 130-5144-900",
"How does the QSFP-DD module handle 400Gb/s transport applications?",
"what is the ETM support status of WL6e_S_85p3GBd_800G_E_STD_PTM3_NMM2 ETM",
"Does this WL6e_S_170p0GBd_600G_E_STD_PTM3_NMM2 ETM updated in multiple releases? list down the updates",
"What are the supported data rates for QSFP-DD Active Optical Cables?",
"List down all the transceiver approved by me",
"How do diagnostic timestamps differ between network element and Site Manager OS time zone?",
"How many ETMs are placed in a particular release",
"What is the value of line code for 130-5144-900",
"What is the latest version for NTTP11AFE6",
"list down latest changes on transceiver pec NTTP11AFE6",
"How do OSFP pluggables support 1.6Tb/s transport?",
"List down all the compatible components for 130-4476-940",
"where was this ETM WL6e_S_170p0GBd_600G_E_STD_PTM3_NMM2 PLM requirement placed",
"how many transceivers are there in optical category",
"What are the specifications for QSFP-DD800 pluggables used in Waveserver 5?",
"What is the typical power consumption of QSFP-DD pluggables at ambient temperature?",
"What is the latest version for 160-9460-010",
"What are the provisioning rules for OTN payload terminating remote endpoints?",
"Can you explain the differences between 400GBASE-SR8 and 400GBASE-DR4 classifications?",
"list down all the components added newly in the latest version for 130-4476-940",
"Give me files attached in workspace for 130-4476-940",
"Does this ETM WL6e_S_170p0GBd_600G_E_STD_PTM3_NMM2 have warnings tracked",
"show me the image of transceiver pec NTTP58BD",
"Show all customers that begin with Liberty",
"Can you provide an overview of documentation roadmap for Waveserver 5?",
"who are the primary/secondary approver for 160-9460-010",
"what are features and benefits of 130-4476-940",
"How can I perform a manual switch to a specific user protection route for SNC?",
"Which customers have the longest fiber spans by distance",
"who are the primary/secondary approver for 130-4476-940",
"What is the significance of Mesh Restorable parameter in SNC configurations?",
"What is the approval status for NTTP11AFE6",
"How can I add or edit routing profiles in control plane?",
"What is the application of 100GBASE-SR4 pluggables in Waveserver?",
"Give me files attached in workspace for 130-5144-900",
"Show all network elements, quantity and software release by customer",
"What is the value of line code for 130-4476-940",
"What is the approval status for 130-4476-940",
"list down all the components added newly in the latest version for 160-9460-010",
"What are the key features of WaveLogic 5n coherent pluggable modules?",
"Count OMS links by customer",
"give me the PLM requirement of WL6e_S_170p0GBd_600G_E_STD_PTM3_NMM2 ETM release-wise",
"Show all network elements, quantity and software release for google and liberty global",
"How is the power budget calculated for pluggable modules in Waveserver 5 system?",
"What is the latest version for 130-4476-940",
"Show all network elements, quantity and software release for google and libertyglobal",
"What are the differences between single-mode fiber (SMF) and multi-mode fiber (MMF)?",
"Show all network elements, quantity and software release by customer by capture ID",
"list down all the components added newly in the latest version for NTTP11AFE6",
"Give me files attached in workspace for NTTP58BD",
"what are features and benefits of 130-5144-900",
"who are the primary/secondary approver for NTTP11AFE6",
"In which WL6e MR release WL6e_S_170p0GBd_600G_E_STD_PTM3_NMM2 ETM was approved",
"What are the steps to retrieve OSRP provisioning information for a network element?",
"Do we want to give option to edit the chat in chatbot?",
"What is the value of line code for NTTP11AFE6",
"What is the significance of IEEE standards in pluggable specifications?",
"Can you explain the blocked node feature in OSRP provisioning process?",
"Which customers have more than 100 network elements of type 6500",
"How does the manual reversion process work for SNC?",
"search all attributes for 160-9460-010 pec for optical category",
"What is the purpose of Time of Day Reversion (TODR) profiles in control plane configuration?",
"What does the term multi-source agreement mean in the context of CFP2-DCO modules?",
"What is the value of line code for NTTP58BD",
"Give me files attached in workspace for NTTP11AFE6",
"What is the approval status for NTTP58BD",
"What are the confidentiality obligations for using Ciena software?",
"list down all the components added newly in the latest version for NTTP58BD",
"What is the approval status for 160-9460-010",
"What is the value of line code for 160-9460-010",
"Give me files attached in workspace for 160-9460-010",
"give me a brief description for transceiver pec NTTP58BD",
"What is the latest version for NTTP58BD",
"who are the primary/secondary approver for NTTP58BD",
]


def main() -> None:
    samples = parse_training_csv(repo_root / "data" / "training_samples.csv")
    router = train_router(samples)
    out = []
    for q in QUESTIONS:
        r = result_to_dict(router.detect(q))
        out.append({"question": q, **r})
    out_path = repo_root / "data" / "question_test_results.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {len(out)} predictions to {out_path}")


if __name__ == "__main__":
    main()
