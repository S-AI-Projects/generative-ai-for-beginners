
import argparse
import json
import sys

# Mock local parameter manifest.
PARAMETERS = {
    "encoder.weight": 100,
    "head.weight": 20,
}


def count_parameters(parameters, freeze_prefix):
    if not isinstance(parameters, dict) or not parameters:
        raise ValueError("Parameters must be a non-empty dictionary.")

    if not isinstance(freeze_prefix, str) or not freeze_prefix:
        raise ValueError("Freeze prefix must be a non-empty string.")

    for name, count in parameters.items():
        if not isinstance(name, str) or not name:
            raise ValueError("Parameter names must be non-empty strings.")
        if type(count) is not int or count <= 0:
            raise ValueError("Parameter counts must be positive integers.")

    matched = [
        name for name in parameters
        if name.startswith(freeze_prefix)
    ]

    total = sum(parameters.values())
    frozen = sum(parameters[name] for name in matched)
    trainable = total - frozen

    trace = [
        {
            "step": "read_manifest",
            "parameter_names": list(parameters.keys()),
            "total": total,
        },
        {
            "step": "apply_freeze_rule",
            "freeze_prefix": freeze_prefix,
            "matched_names": matched,
            "frozen": frozen,
        },
        {
            "step": "calculate_trainable",
            "trainable": trainable,
        },
    ]

    return {
        "total": total,
        "frozen": frozen,
        "trainable": trainable,
        "matched_names": matched,
        "unmatched_prefix": not matched,
        "trace": trace,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prefix",
        default="encoder",
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "boundary", "unmatched"],
        default="normal",
    )
    args = parser.parse_args()

    parameters = PARAMETERS

    if args.scenario == "boundary":
        parameters = {"encoder.weight": 1, "head.weight": 1}
    elif args.scenario == "unmatched":
        pass

    prefix = "missing_layer" if args.scenario == "unmatched" else args.prefix

    try:
        result = count_parameters(parameters, prefix)
        print(json.dumps(result, indent=2))
        return 0
    except ValueError as error:
        print("ERROR:", error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

