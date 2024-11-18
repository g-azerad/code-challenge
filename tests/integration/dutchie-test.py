import sys
import time

import requests

products_by_dispensary = {
    'Garden Greenz': {
        'Flower1': "https://dutchie.com/dispensary/garden-greenz/product/old-pal-ready-to-roll-strawnana-7g",
        'Flower2': "https://dutchie.com/dispensary/garden-greenz/product/66a2c25961451f0001b05610",
        'Pre-rolls': "https://dutchie.com/dispensary/garden-greenz/product/6650f72f36cb7c0001923a85",
        'Vaporizer': "https://dutchie.com/dispensary/garden-greenz/product/66a2c25961451f0001b05611"
    },
    'Cream': {
        'Flower1': 'https://dutchie.com/dispensary/cream1/product/happy-hour-21',
        'Flower2': 'https://dutchie.com/dispensary/cream1/product/sweet-jealousy',
        'Vaporizer': 'https://dutchie.com/dispensary/cream1/product/energize-disposable',
        'Edible': 'https://dutchie.com/dispensary/cream1/product/mile-high-mint-10-pack-chocolate-bar-100mg'
    },
    'Dazed': {
        'Vaporizer': 'https://dutchie.com/dispensary/dazed-cannabis1/product/full-moon-moonrocks-2g',
        'Flower': 'https://dutchie.com/dispensary/dazed-cannabis1/product/baby-yoda-3-5g',
        'Concentrate': 'https://dutchie.com/dispensary/dazed-cannabis1/product/diamond-powder-5g-95210',
        'Oral': 'https://dutchie.com/dispensary/dazed-cannabis1/product/bliss-pouch-5mg-2pck-1906-87559'
    },
    'Cookies Harrison': {
        'Edible': 'https://dutchie.com/dispensary/cookies-harrison/product/cookies-small-batch-salted-carmel',
        'Flower': 'https://dutchie.com/dispensary/cookies-harrison/product/bat-sh-t',
        'Pre-roll': 'https://dutchie.com/dispensary/cookies-harrison/product/a-happy-hybrid-6pk',
        'Concentrate': 'https://dutchie.com/dispensary/cookies-harrison/product/apple-crisp-live-resin-badder'
    }
}

base_url = "http://localhost:8000/"

def main():
    try:
        if len(sys.argv) > 1:
            filtered_products = {sys.argv[1]: products_by_dispensary[sys.argv[1]]}
        else:
            filtered_products = products_by_dispensary
        for dispensary, products in filtered_products.items():
            print(f'Testing dispensary {dispensary}')
            cart_id = post_request(f'{base_url}/carts').json()['cart_id']
            print(f'Created cart {cart_id}')
            for category, product_url in products.items():
                add_product_body = {
                    'product_url': product_url,
                    'quantity': 1
                }
                add_product_res = post_request(f'{base_url}/carts/{cart_id}/add-product', data=add_product_body).json()
                print(f'Added product {product_url}: {add_product_res['product_id']}')
                time.sleep(2)
            verify_cart = requests.get(f'{base_url}/carts/{cart_id}/verify')
            print(f'Verify Cart result:{verify_cart.json()}')
            post_request(f'{base_url}/carts/{cart_id}/proceed-checkout')
            print(f'Proceeded to checkout')
            submit_order_body = {
                'first_name': "Peter",
                'last_name': "Griffin",
                'mobile_phone': "718-123-4567",
                'birthdate': "2000-01-01",
                'email': "demo@kuuli.es",
                'state': "IL"
            }
            submit_order_response = post_request(f'{base_url}/carts/{cart_id}/submit-order', data=submit_order_body)
            print(f'Order created: {submit_order_response.json()}')
            print('======================================================\n\n')
    except requests.exceptions.HTTPError as e:
        response = e.response
        print(f'HTTP Error during request {e.request.url} with data {e.request.body}')
        print(f'code={response.status_code} msg={response.text}')

def post_request(url, data=None):
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response


if __name__ == "__main__":
    main()