
def get_index_by_prop(array, value, prop = 'id'):
    return next((i for i, item in enumerate(array) if item[prop] == value), -1)