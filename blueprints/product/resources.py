from flask import Blueprint
from flask_restful import Api, Resource, reqparse, marshal
from blueprints import db
from blueprints.product.models import Product, Price, Photo, Description
from datetime import datetime, timedelta
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
        if args["product_link"]:
            end_index = args["product_link"].find("html")+4
            if end_index == 3:
                return {
                    "status": "FAILED",
                    "message": "Incorrect Fabelio product link address."
                }, 400, {"Content-Type": "application/json"}
            product_link = args["product_link"][:end_index]
            product_response = requests.get(product_link)
            
            # check if response is OK
            if product_response.status_code == 200:
                # check if product link is already exist
                if Description.query.filter_by(link=product_link).all():
                    return {
                        "status": "FAILED",
                        "message": "Product link already exists."
                    }, 400, {"Content-Type": "application/json"}
                soup = BeautifulSoup(product_response.text, "html.parser")
                scrap_product_description = soup.find(id="description")
                if scrap_product_description is not None:
                    product_description = " ".join(scrap_product_description.stripped_strings)
                    # add new description to db session
                    new_description = Description(product_description, product_link)
                    db.session.add(new_description)
                    db.session.commit()

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
                                    variant_id = variant["products"][0]
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
                    db.session.commit()
                    return {
                        "status": "SUCCESS",
                        "message": "Product is successfully recorded.",
                        "product_parent_id": int(product_id)
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

    def options(self):
        return 200


class ShowProducts(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "order", location="args", default="created",
            choices=("created", "name", ""),
            help="Input must be 'created' or 'name'"
        )
        parser.add_argument(
            "sort", location="args", default="desc",
            choices=("asc", "desc", ""),
            help="Input must be 'asc' or 'desc'"
        )
        parser.add_argument("page", type=int, location="args", default=1)
        parser.add_argument("per_page", type=int, location="args", default=10)
        args = parser.parse_args()

        product_query = Product.query.filter_by(parent_id=None)
        # order result
        if args["order"] is not None:
            # order product by name
            if args["order"] == "name":
                if args["sort"] == "desc" or args["sort"] == "":
                    product_query = product_query.order_by(Product.name.desc())
                elif args["sort"] == "asc":
                    product_query = product_query.order_by(Product.name.asc())
            # order product by date created
            elif args["order"] == "created" or args["order"] == "":
                if args["sort"] == "desc" or args["sort"] == "":
                    product_query = product_query.order_by(Product.created.desc())
                elif args["sort"] == "asc":
                    product_query = product_query.order_by(Product.created.asc())
        
        # limit shown products per page
        product_total = len(product_query.all())
        offset = (args["page"] - 1)*args["per_page"]
        product_query = product_query.limit(args["per_page"]).offset(offset)
        if product_total%args["per_page"] != 0 or product_total == 0:
            page_total = int(product_total/args["per_page"]) + 1
        else:
            page_total = int(product_total/args["per_page"])
        response = {
            "product_total": product_total, "page":args["page"],
            "page_total":page_total, "per_page":args["per_page"]
        }

        all_products = []
        for each_product in product_query:
            product_info = marshal(each_product, Product.response)
            product_info["product_link"] = each_product.description.link
            all_products.append(product_info)
        response["all_products"] = all_products
        return response, 200, {"Content-Type": "application/json"}

    def options(self):
        return 200


class UpdatePrice(Resource):
    def put(self):
        parent_products = Product.query.filter_by(parent_id=None)
        for each_parent in parent_products.all():
            product_children = each_parent.product_children
            if product_children == []:
                # check if last updated price is within an hour
                if each_parent.price[-1].created+timedelta(hours=1) <= datetime.now():
                    # get new product_parent info
                    product_parent_info_response = requests.get("https://fabelio.com/insider/data/product/id/"+str(each_parent.id))
                    product_parent_info_json = product_parent_info_response.json()
                    # add new product_parent price
                    product_parent_price = Price(
                        product_id=each_parent.id,
                        unit_price=product_parent_info_json["product"]["unit_price"],
                        unit_sale_price=product_parent_info_json["product"]["unit_sale_price"]
                    )
                    db.session.add(product_parent_price)
            elif product_children != []:
                for each_child in product_children:
                    # check if last updated price is within an hour
                    if each_child.price[-1].created+timedelta(hours=1) <= datetime.now():
                        variant_id = each_child.id
                        # get new variant info
                        variant_info_response = requests.get("https://fabelio.com/insider/data/product/id/"+str(variant_id))
                        variant_info_json = variant_info_response.json()
                        # add new variant price
                        variant_price = Price(
                            product_id=variant_id,
                            unit_price=variant_info_json["product"]["unit_price"],
                            unit_sale_price=variant_info_json["product"]["unit_sale_price"]
                        )
                        db.session.add(variant_price)
        db.session.commit()
        return {
            "status": "SUCCESS",
            "message": "Products are successfully updated."
        }, 200, {"Content-Type": "application/json"}

    def options(self):
        return 200


class ShowProductDetail(Resource):
    def get(self, id=None):
        if id is not None:
            pass
        return {
            "status": "NOT_FOUND",
            "message": "Product ID is not found."
        }, 404, {"Content-Type": "application/json"}

    def options(self, id=None):
        return 200


api.add_resource(AddProduct, "/add_product")
api.add_resource(ShowProducts, "/show_products")
api.add_resource(UpdatePrice, "/update_price")
api.add_resource(ShowProductDetail, "/product_detail/<int:id>")
