from flask import Blueprint
from flask_restful import Api, Resource, reqparse, marshal
from blueprints import db
from blueprints.product.models import Product, Price, Photo, Description
from datetime import datetime
from bs4 import BeautifulSoup
import requests, re, json


product_blueprint = Blueprint("product", __name__)
api = Api(product_blueprint)


class AddProduct(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("product_link", location="json", required=True)
        args = parser.parse_args()

        # scrap product details only if input is not empty
        if args["product_link"] is not None:
            end_index = args["product_link"].find("html")+4
            if end_index == -1:
                return {
                    "status": "FAILED",
                    "message": "Incorrect Fabelio product link address."
                }, 400, {"Content-Type": "application/json"}
            product_link = args["product_link"][:end_index]
            product_response = requests.get(product_link)
            
            # check if response is OK
            if product_response.status_code == 200:
                soup = BeautifulSoup(product_response.text, "html.parser")
                scrap_product_description = soup.find(id="description")
                if scrap_product_description is not None:
                    product_description = " ".join(scrap_product_description.stripped_strings)
                    # add new description to db session
                    new_description = Description(product_description, product_link)
                    db.session.add(new_description)
                    
                    # scrap base product
                    scrap_product = soup.find(id="product-ratings")
                    if scrap_product is not None:
                        product_id = scrap_product["data-product-id"]
                        product_parent_response = requests.get("https://fabelio.com/insider/data/product/id/"+str(product_id))
                        product_parent_json = product_parent_response.json()
                        # add new product to db session
                        product_parent = Product(
                            id=int(product_id),
                            parent_id=None,
                            description_id=new_description.id,
                            name=product_parent_json["product"]["name"]
                        )
                        db.session.add(product_parent)
                        # add initial price to db session
                        product_parent_price = Price(
                            product_id=product_parent.id,
                            unit_price=product_parent_json["product"]["unit_price"],
                            unit_sale_price=product_parent_json["product"]["unit_sale_price"]
                        )
                        db.session.add(product_parent_price)
                        # get product photos
                        product_parent_gallery_response = requests.get(
                            "https://fabelio.com/swatches/ajax/media/",
                            params={"product_id": product_id}
                        )
                        product_parent_gallery_json = product_parent_gallery_response.json()
                        # add product parent photos to db session
                        for product_parent_photo in product_parent_gallery_json["gallery"].values():
                            db.session.add(
                                Photo(
                                    product_id=product_parent.id,
                                    source=product_parent_photo["large"]
                                )
                            )
                        
                        # scrap variant product
                        scrap_variants = soup.find(text=re.compile("(data-role=swatch-options)"))
                        if scrap_variants is not None:
                            scrap_variants_json = json.loads(scrap_variants)
                            variants_data = scrap_variants_json["[data-role=swatch-options]"]["Magento_Swatches/js/swatch-renderer"]
                            special_num_dict = variants_data["jsonSwatchConfig"]
                            special_num = list(special_num_dict.keys())[0]
                            variants = variants_data["jsonConfig"]["attributes"][special_num]["options"]
                            for variant in variants:
                                if variant["products"] != []:
                                    variant_id = variant["products"]
                                    variant_info_response = requests.get("https://fabelio.com/insider/data/product/id/"+str(variant_id))
                                    variant_info_json = variant_info_response.json()
                                    db.session.add(
                                        Product(
                                            id=int(variant_id),
                                            parent_id=product_parent.id,
                                            description_id=new_description.id,
                                            name=variant_info_json["product"]["name"]
                                        )
                                    )
                                    # add initial price to db session
                                    variant_price = Price(
                                        product_id=variant_id,
                                        unit_price=variant_info_json["product"]["unit_price"],
                                        unit_sale_price=variant_info_json["product"]["unit_sale_price"]
                                    )
                                    db.session.add(variant_price)
                                    # get product variant photos
                                    variant_gallery_response = requests.get(
                                        "https://fabelio.com/swatches/ajax/media/",
                                        params={"product_id": variant_id}
                                    )
                                    variant_gallery_json = variant_gallery_response.json()
                                    # add product variant photos to db session
                                    for variant_photo in variant_gallery_json["gallery"].values():
                                        db.session.add(
                                            Photo(
                                                product_id=variant_id,
                                                source=variant_photo["large"]
                                            )
                                        )
                    return {
                        "status": "SUCCESS",
                        "message": "Product is successfully recorded."
                    }, 200, {"Content-Type": "application/json"}
                return {
                    "status": "NOT_FOUND",
                    "message": "Product info cannot be found."
                }, 404, {"Content-Type": "application/json"}
            return {
                "status": "FAILED",
                "message": "Failed to load link address."
            }, 400, {"Content-Type": "application/json"}
        return {
            "status": "FAILED",
            "message": "Product link cannot be empty."
        }, 400, {"Content-Type": "application/json"}


api.add_resource(AddProduct, "/add_product")
