import sys
from input_parser import parse_args
from debug_log import print_log
from image_utils import export_images, import_images, resize_images
from session import clear_temp, get_session

if __name__ == "__main__":
    # session_id = None
    # images_path = ["/Users/ro7rinke/Desktop/cards_against_humani_24.png"]
    old_images_info = []
    all_images_info = []
    error_images_info = []
    selected_images = []

    def get_selected_images_info():
        return next(image_info for image_info in enumerate(all_images_info) if image_info.get('id') in selected_images)

    def resize(input_dict):
        params_filter = ['width', 'height', 'dpi', 'sacale']
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        result_new_images_info, result_old_images_info, result_error_images_info = resize_images(all_images_info, **params)
        print_log(result_new_images_info, title = 'Resized images')
        print_log(result_old_images_info, title='Old Images')
        print_log(result_error_images_info, type='error', level=1, title='Error resize')

    def save_images(input_dict):
        params_filter = ['output_directory_path']
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        success_images_info, error_images_info = export_images(all_images_info, **params)
        print_log(success_images_info, title='Salvos com sucesso', level=1)
        print_log(error_images_info, title='Erros ao salvar', type='error', level=1)

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

        if input_dict.get('clear_all'):
            clear_temp()

        if input_dict.get('action') is not None:
            match input_dict.get('action'):
                case 'resize':
                    resize(input_dict)
                case 'save_images':
                    save_images(input_dict)
                case _:
                    print_log('Invalid action', type='error', level=1)

        if input_dict.get('exit'):
            break
