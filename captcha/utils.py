from django.utils.crypto import salted_hmac


def encode_solution(salt, solution):
    return salted_hmac(salt, solution).hexdigest()
