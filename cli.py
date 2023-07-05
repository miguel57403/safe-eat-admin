from commands.database_feed import database_feed
from commands.database_clear import database_clear
from commands.database_count import database_count
import commands.update_images as update_images

# MONGO_URL = "mongodb+srv://a57403:UmCcYuRPzdDG7QDK@safeeat.xbbss2l.mongodb.net/safeeatdb?retryWrites=true&w=majority" # atlas
MONGO_URL = "mongodb://localhost:27017"  # local
# BASE_URL = "https://safe-eat-api.azurewebsites.net" # azure
BASE_URL = "http://localhost:8080"  # local
SAVE_IMAGES = False


def get_parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='App tools')
    subparsers = parser.add_subparsers(dest='command')

    database_feed_parser = subparsers.add_parser('database:feed')
    database_feed_parser.add_argument('-u', '--url', default=BASE_URL)
    database_feed_parser.add_argument(
        '-s', '--save-images', action='store_true', default=SAVE_IMAGES)

    database_clear_parser = subparsers.add_parser('database:clear')
    database_clear_parser.add_argument('-u', '--mongo-url', default=MONGO_URL)

    database_count_parser = subparsers.add_parser('database:count')
    database_count_parser.add_argument('-u', '--mongo-url', default=MONGO_URL)

    topics = ['advertisements', 'restaurants']
    for it in topics:
        update_images_parser = subparsers.add_parser(f'update_images:{it}')
        update_images_parser.add_argument('-u', '--url', default=BASE_URL)

    return parser


if __name__ == '__main__':
    parser = get_parse_args()
    args = parser.parse_args()
    if args.command == 'database:feed':
        database_feed(args.url, args.save_images)
    elif args.command == 'database:clear':
        database_clear(args.mongo_url)
    elif args.command == 'database:count':
        database_count(args.mongo_url)
    elif args.command == 'update_images:advertisements':
        update_images.advertisements(args.url)
    elif args.command == 'update_images:restaurants':
        update_images.restaurants(args.url)
    else:
        parser.print_help()
