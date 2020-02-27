# Fabelio Price Monitoring API

## API Endpoints
**API Domain:** 
> https://wildan-price-monitoring.herokuapp.com/
| Endpoint | Method | Description | Request Parameter | Location |
|--|:--:|--|:--:|:--:|
| /add_product | POST | Add new product based on Fabelio product link. | product_link | Body |
| /show_products | GET | List all submitted product links. | order ('name' or 'created'), sort ('asc' or 'desc'), page, per_page | Query Params |
| /update_price | PUT | Update all products price hourly. | - | - |
| /product_detail/<int:id> | GET | Get product detail based on product ID. | - | - |
