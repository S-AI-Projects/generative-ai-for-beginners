"""Local model-manifest selection teaching example."""

FIXTURE = [
    {"name": "Model C", "context": 1024},
    {"name": "Model A", "ram": 4, "context": 2048},
    {"name": "Model B", "ram": 8, "context": 4096},
]


def select_models(manifest, ram_budget, requested_context):
    eligible = []
    excluded = []

    for model in manifest:
        name = model.get("name", "Unknown model")

        if "ram" not in model or "context" not in model:
            excluded.append((name, "Missing required RAM or context data"))
            continue

        if not isinstance(model["ram"], int) or not isinstance(
            model["context"], int
        ):
            excluded.append((name, "RAM and context must be integers"))
            continue

        if model["ram"] <= 0 or model["context"] <= 0:
            excluded.append((name, "RAM and context must be positive"))
            continue

        if model["ram"] > ram_budget:
            excluded.append((name, "Insufficient RAM"))
            continue

        if model["context"] < requested_context:
            excluded.append((name, "Insufficient context"))
            continue

        eligible.append(name)

    return eligible, excluded


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scenario",
        choices=["normal", "boundary", "failure"],
    )
    args = parser.parse_args()

    ram_budget = 6
    requested_context = 1024

    if args.scenario == "boundary":
        ram_budget = 4
        requested_context = 2048

    if args.scenario == "failure":
        print("ERROR: Model C is missing required RAM data.")
        print("RECOVERY: Skipping Model C and checking the next entry.")

    eligible, excluded = select_models(
        FIXTURE, ram_budget, requested_context
    )

    print("Eligible:", eligible)

    for name, reason in excluded:
        print("Excluded:", name, "-", reason)


if __name__ == "__main__":
    main()
