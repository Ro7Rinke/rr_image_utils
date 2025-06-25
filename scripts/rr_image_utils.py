import sys
from input_parser import parse_args
from debug_log import print_log
from image_utils import import_images
from session import clear_temp, get_session

if __name__ == "__main__":
    # session_id = None
    # images_path = ["/Users/ro7rinke/Desktop/cards_against_humani_24.png"]
    old_images_info = []
    all_images_info = []
    selected_images = []

    def get_selected_images_info():
        return next(image_info for image_info in enumerate(all_images_info) if image_info.get('id') in selected_images)


    args_string = " ".join(sys.argv[1:])

    args_string = args_string or input()
    args_dict = parse_args(args_string)
    print_log(args_dict, title='Parsed ARGS')

    session_id = args_dict.get('session_id')
    images_path = args_dict.get('images_path', [])
    images_path = [images_path] if isinstance(images_path, str) else images_path

    session_id = get_session(session_id)

    all_images_info, error_images_info = import_images(session_id, images_path)
    print_log(all_images_info, title='Imported images info')

    while True:
        input_string = input()
        input_dict = parse_args(input_string)

        match input_dict.get('action'):
            case 'clear_all':
                clear_temp()
            case 'exit':
                break
            case _:
                print_log('Invalid action', type='error', level=1)

