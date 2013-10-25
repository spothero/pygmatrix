import base64
import hashlib
import hmac
from itertools import izip_longest
import requests
import anyjson as json

def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

class PyGMatrix(object):
    def __init__(self, matrix_url=None, client_id=None, secret_key=None):
        if not matrix_url:
            self.matrix_url = 'https://maps.googleapis.com/maps/api/distancematrix/json'

        if bool(client_id) != bool(secret_key):
            raise ValueError("You must have both a client_id and secret_key, not just one.")

        if client_id and secret_key:
            self.client_id = client_id
            self.secret_key = secret_key
        else:
            self.client_id = None
            self.secret_key = None

    def get_distances(self, origins=[], destinations=[], sensor=False, **kwargs):
        """
        Simple consumer for the Google distance matrix api.return_dict

        Pass origins and destinations to this function. Origins and destinations can be in the form of an address or
        latitude,longitude combinations.
        """

        if isinstance(origins, str):
            origins = [origins]

        if isinstance(destinations, str):
            destinations = [destinations]

        origins_str = '|'.join(origins)

        destinations_str = '|'.join(destinations)

        if sensor:
            sensor_str = 'true'
        else:
            sensor_str = 'false'

        payload = dict(
            origins=origins_str,
            destinations=destinations_str,
            sensor=sensor_str
        )

        payload.update(kwargs)

        req = requests.Request('GET', self.matrix_url, params=payload)
        prepared_request = req.prepare()

        if len(prepared_request.path_url) > 1900:
            # Our request is too long, break it down
            # Divide the number of origins into two and call again
            if len(origins) > 1:
                sub_response_top = self.get_distances(origins=origins[:len(origins)/2], destinations=destinations,
                                                      sensor=sensor, **kwargs)
                sub_response_bottom = self.get_distances(origins=origins[len(origins)/2:], destinations=destinations,
                                                         sensor=sensor, **kwargs)

                if not isinstance(sub_response_top, dict):
                    # There was a request error.
                    return sub_response_top

                if not isinstance(sub_response_bottom, dict):
                    # There was a request error.
                    return sub_response_bottom

                # Combine them
                response = sub_response_top
                response['rows'] += sub_response_bottom['rows']
                response['origin_addresses'] += sub_response_bottom['origin_addresses']

                if 'statuses' not in response.keys():
                    response['statuses'] = [sub_response_bottom['status']]
                else:
                    response['statuses'].append(sub_response_bottom['status'])


            else:
                # Start dividing on destinations
                sub_response_left = self.get_distances(origins=origins, destinations=destinations[:len(destinations)/2],
                                                       sensor=sensor, **kwargs)
                sub_response_right = self.get_distances(origins=origins, destinations=destinations[len(destinations)/2:],
                                                        sensor=sensor, **kwargs)

                if not isinstance(sub_response_left, dict):
                    # There was a request error.
                    return sub_response_left

                if not isinstance(sub_response_right, dict):
                    # There was a request error.
                    return sub_response_right

                # Combine them
                response = sub_response_left
                row_index = 0
                for row in sub_response_right['rows']:
                    response['rows'][row_index]['elements'] += sub_response_right['rows'][row_index]['elements']
                response['destination_addresses'] += sub_response_right['destination_addresses']

                if 'statuses' not in response.keys():
                    response['statuses'] = [sub_response_right['status']]
                else:
                    response['statuses'].append(sub_response_right['status'])

            return response

        if self.client_id:
            # Do signing black magic
            payload.update(dict(client=self.client_id))

            req = requests.Request('GET', self.matrix_url, params=payload)
            prepared_request = req.prepare()

            decoded_key = base64.urlsafe_b64decode(self.secret_key)

            # Create a signature using the private key and the URL-encoded
            # string using HMAC SHA1. This signature will be binary.
            signature = hmac.new(decoded_key, prepared_request.path_url, hashlib.sha1)

            # Encode the binary signature into base64 for use within a URL
            encoded_signature = base64.urlsafe_b64encode(signature.digest())

            payload.update(dict(signature=encoded_signature))

        response = requests.get(self.matrix_url, params=payload)

        if response.status_code == 200:
            return_dict = json.loads(response.content)

            return return_dict

        return response

