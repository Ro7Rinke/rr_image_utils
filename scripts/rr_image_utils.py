import shlex
import sys
from input_parser import parse_args
from debug_log import print_log
from image_utils import convert_images_to_avif, convert_images_to_jpeg, edit_border_images, export_images, export_to_pdf, export_to_word, images_from_grid, import_images, import_images_from_pdf, noise_images, quicklook_images, resize_images
from session import clear_temp, get_session

if __name__ == "__main__":
    # session_id = None
    # images_path = ["/Users/ro7rinke/Desktop/cards_against_humani_24.png"]
    old_images_info = []
    all_images_info = []
    error_images_info = []
    selected_images = []

    def get_selected_images_info():
        global old_images_info, all_images_info, error_images_info, selected_images
        return next(image_info for image_info in enumerate(all_images_info) if image_info.get('id') in selected_images)

    def resize(input_dict):
        global old_images_info, all_images_info, error_images_info, selected_images
        params_filter = ['width', 'height', 'dpi', 'scale']
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        result_new_images_info, result_old_images_info, result_error_images_info = resize_images(all_images_info, **params)
        print_log(result_new_images_info, title = 'Resized images')
        print_log(result_old_images_info, title='Old Images')
        print_log(result_error_images_info, type='error', level=1, title='Error resize')
        all_images_info = result_new_images_info
        error_images_info = result_error_images_info
        old_images_info = result_old_images_info

    def save_images(input_dict):
        global old_images_info, all_images_info, error_images_info, selected_images
        params_filter = ['output_directory_path', 'with_id', 'prefix', 'sufix']
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        result_success_images_info, result_error_images_info = export_images(all_images_info, **params)
        print_log(result_success_images_info, title='Salvos com sucesso', level=1)
        print_log(result_error_images_info, title='Erros ao salvar', type='error', level=1)
        all_images_info = result_success_images_info
        error_images_info = result_error_images_info

    def to_word(input_dict):
        global old_images_info, all_images_info, error_images_info, selected_images
        params_filter = ['output_directory_path', 'dpi', 'file_name']
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        result_success_images_info, result_error_images_info = export_to_word(all_images_info, **params)
        print_log(result_success_images_info, title='Salvos com sucesso', level=1)
        print_log(result_error_images_info, title='Erros ao salvar', type='error', level=1)
        all_images_info = result_success_images_info
        error_images_info = result_error_images_info

    def to_pdf(input_dict):
        global old_images_info, all_images_info, error_images_info, selected_images
        params_filter = ['output_directory_path', 'dpi', 'file_name']
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        result_success_images_info, result_error_images_info = export_to_pdf(all_images_info, **params)
        print_log(result_success_images_info, title='Exportadas para PDF com sucesso', level=1)
        print_log(result_error_images_info, title='Erros ao exportar para PDF', type='error', level=1)
        all_images_info = result_success_images_info
        error_images_info = result_error_images_info

    def from_grid(input_dict):
        global old_images_info, all_images_info, error_images_info, selected_images
        params_filter = ['cols', 'rows']
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        result_success_images_info = images_from_grid(all_images_info, **params)
        print_log(result_success_images_info, title='Grid recortado')
        all_images_info = result_success_images_info

    def preview_images(input_dict):
        global old_images_info, all_images_info, error_images_info, selected_images
        quicklook_images(all_images_info)

    def to_jpeg(input_dict):
        global old_images_info, all_images_info, error_images_info, selected_images
        params_filter = ['dpi', 'quality', 'background_color']
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        result_new_images_info, result_old_images_info, result_error_images_info = convert_images_to_jpeg(all_images_info, **params)
        print_log(result_new_images_info, title='Convertidas para JPEG com sucesso', level=1)
        print_log(result_error_images_info, title='Erros ao converter para JPEG', type='error', level=1)
        all_images_info = result_new_images_info
        error_images_info = result_error_images_info
        old_images_info = result_old_images_info

    def to_avif(input_dict):
        global old_images_info, all_images_info, error_images_info, selected_images
        params_filter = ['dpi', 'quality', 'speed', 'no_alpha', 'subsampling', 'color']
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        result_new_images_info, result_old_images_info, result_error_images_info = convert_images_to_avif(all_images_info, **params)
        print_log(result_new_images_info, title='Convertidas para AVIF com sucesso', level=1)
        print_log(result_error_images_info, title='Erros ao converter para AVIF', type='error', level=1)
        all_images_info = result_new_images_info
        error_images_info = result_error_images_info
        old_images_info = result_old_images_info

    def remove_noise(input_dict):
        global old_images_info, all_images_info, error_images_info, selected_images
        params_filter = []
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        result_new_images_info, result_old_images_info, result_error_images_info = noise_images(all_images_info)
        print_log(result_new_images_info, title='Noise removido com sucesso', level=1)
        print_log(result_error_images_info, title='Erros ao remover noise', type='error', level=1)
        all_images_info = result_new_images_info
        error_images_info = result_error_images_info
        old_images_info = result_old_images_info

    def crop(input_dict):
        global old_images_info, all_images_info, error_images_info, selected_images
        params_filter = ["left", "right", "top", "bottom", "scale", "type", "color", "dpi", "threshold"]
        params = {key: input_dict[key] for key in params_filter if key in input_dict}
        result_new_images_info, result_old_images_info, result_error_images_info = edit_border_images(all_images_info, **params)
        print_log(result_new_images_info, title='Recortadas com sucesso', level=1)
        print_log(result_error_images_info, title='Erros ao recortar', type='error', level=1)
        all_images_info = result_new_images_info
        error_images_info = result_error_images_info
        old_images_info = result_old_images_info

    args_string = " ".join(shlex.quote(arg) for arg in sys.argv[1:])

    args_string = args_string or input()
    args_dict = parse_args(args_string)
    print_log(args_dict, title='Parsed ARGS')

    session_id = args_dict.get('session_id')
    is_pdf = args_dict.get('pdf')
    images_path = args_dict.get('images_path', [])
    images_path = [images_path] if isinstance(images_path, str) else images_path
    params_filter = ['dpi', 'page_as_image']
    params = {key: args_dict[key] for key in params_filter if key in args_dict}

    session_id = get_session(session_id)

    all_images_info, error_images_info = import_images_from_pdf(session_id, images_path, **params) if is_pdf else import_images(session_id, images_path)
    print_log(all_images_info, title='Imported images info')

    while True:
        input_string = input()
        input_dict = parse_args(input_string)

        if input_dict.get('action') is not None:
            match input_dict.get('action'):
                case 'resize':
                    resize(input_dict)
                case 'save_images':
                    save_images(input_dict)
                case 'to_word':
                    to_word(input_dict)
                case 'to_pdf':
                    to_pdf(input_dict)
                case 'from_grid':
                    from_grid(input_dict)
                case 'preview':
                    preview_images(input_dict)
                case 'to_jpeg':
                    to_jpeg(input_dict)
                case 'to_avif':
                    to_avif(input_dict)
                case 'remove_noise':
                    remove_noise(input_dict)
                case 'crop':
                    crop(input_dict)
                case _:
                    print_log('Invalid action', type='error', level=1)

        if input_dict.get('clear_all'):
            clear_temp()

        if input_dict.get('exit'):
            break



# L: 323 R: 191 T: 176 B: 108
# L: 470 R: 248 T: 378 B: 373 16.23 x 25.23 (27.726% X 26.952%) - 23.8 x 16


# /Users/ro7rinke/Library/CloudStorage/GoogleDrive-ro7rinke2@gmail.com/My Drive/BoardGame/Brass Birmingham/final-print/brass-print.pdf