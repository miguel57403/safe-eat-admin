from commands.database_feed import database_feed

# BASE_URL = "https://safe-eat-api.azurewebsites.net"
BASE_URL = "http://localhost:8080"
SAVE_IMAGES = False


def get_parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='PDF tools')
    subparsers = parser.add_subparsers(dest='command')

    database_feed_parser = subparsers.add_parser('database:feed')
    database_feed_parser.add_argument('-u', '--url', default=BASE_URL)
    database_feed_parser.add_argument(
        '-s', '--save-images', action='store_true', default=SAVE_IMAGES)

    return parser


if __name__ == '__main__':
    parser = get_parse_args()
    args = parser.parse_args()
    if args.command == 'database:feed':
        database_feed(args.url, args.save_images)
    else:
        parser.print_help()
