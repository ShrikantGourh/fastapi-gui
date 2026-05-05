from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


from src.domain_intent_model import DomainIntentRouter, parse_training_csv, train_router, result_to_dict


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_path = repo_root / "data" / "training_samples.csv"
    model_path = repo_root / "data" / "domain_intent_router.json"

    samples = parse_training_csv(data_path)
    router = train_router(samples)
    router.save(model_path)
    print(f"Saved model: {model_path}")

    loaded = DomainIntentRouter.load(model_path)
    examples = [
        "list all transceivers",
        "show module details",
        "how many WL6e configs have warning track",
        "compatible components for platform",
    ]

    for question in examples:
        result = loaded.detect(question)
        print("\nQuestion:", question)
        print("Detected:", result_to_dict(result))


if __name__ == "__main__":
    main()
