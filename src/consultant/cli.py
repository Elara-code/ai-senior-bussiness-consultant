import argparse
from uuid import UUID

from consultant.api.dependencies import encode_development_token
from consultant.application.projects import Identity
from consultant.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    token = subparsers.add_parser("dev-token")
    token.add_argument("--organization-id", type=UUID, required=True)
    token.add_argument("--user-id", type=UUID, required=True)
    token.add_argument("--display-name", default="Demo Consultant")
    args = parser.parse_args()
    if args.command == "dev-token":
        identity = Identity(
            organization_id=args.organization_id,
            user_id=args.user_id,
            display_name=args.display_name,
        )
        print(encode_development_token(identity, get_settings().development_auth_secret))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
