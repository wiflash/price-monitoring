from flask import Blueprint
from flask_restful import Api, Resource, reqparse, marshal
from blueprints import db
from blueprints.product.models import Product, Price, Photo, Description, Category
from datetime import datetime
from bs4 import BeautifulSoup
import requests, re, json


product_blueprint = Blueprint("product", __name__)
api = Api(product_blueprint)


class AddProduct(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "product_link", location="json",
            required=True, help="Product link cannot be empty"
        )
        args = parser.parse_args()

        # scrapping product details
        if args["product_link"] is not None:
            product_response = requests.get(args["product_link"])
            soup = BeautifulSoup(product_response.text, "html.parser")
            scrap_product_description = soup.find(id="description")
            if scrap_product_description is not None:
                product_description = " ".join(scrap_product_description.stripped_strings)
                new_description = Description(product_description)
                db.session.add(new_description)
                # scrap base product
                scrap_product = soup.find(id="product-ratings")
                if scrap_product is not None:
                    product_id = scrap_product["data-product-id"]
                    parent_product_response = requests.get("https://fabelio.com/insider/data/product/id/"+str(product_id))
                    parent_product_json = parent_product_response.json()
                    parent_product = Product(product_id, None, new_description.id, parent_product_json.name)
                    db.session.add(parent_product)
                # scrap variant product
                scrap_variants = soup.find(text=re.compile("(data-role=swatch-options)"))
                if scrap_variants is not None:
                    scrap_variants_json = json.loads(scrap_variants)
                    variants_data = scrap_variants_json["[data-role=swatch-options]"]["Magento_Swatches/js/swatch-renderer"]
                    special_num_dict = variants_data["jsonSwatchConfig"]
                    special_num = list(special_num_dict.keys())[0]
                    variants = variants_data["jsonConfig"]["attributes"][special_num]["options"]
                    variants_id = [variant["products"][0] for variant in variants if variant["products"] != []]
                params = {"product_id": product_id}
                product_gallery_response = requests.get("https://fabelio.com/swatches/ajax/media/", params=params)
                product_gallery_json = product_gallery_response.json()
                product_gallery = [picture["large"] for picture in product_gallery_json["gallery"].values()]
                print(product_gallery)

