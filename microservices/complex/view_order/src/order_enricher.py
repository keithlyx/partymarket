from typing import Any, Callable, Dict, Mapping


class OrderEnrichmentError(Exception):
    """A stored order could not be enriched with current descriptions."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _require_success(response: Any, service_name: str) -> Mapping[str, Any]:
    if not isinstance(response, dict):
        raise OrderEnrichmentError(f"{service_name} service returned invalid data.")

    code = response.get("code")
    if not isinstance(code, int) or code not in range(200, 300):
        raise OrderEnrichmentError(f"{service_name} data could not be retrieved.")
    return response


def enrich_order(
    order: Mapping[str, Any],
    fetch_catalogue_item: Callable[[str], Any],
    fetch_venue: Callable[[str], Any],
) -> Dict[str, Any]:
    """Add current descriptions while retaining values stored at purchase time."""
    order_details = dict(order)
    enriched_items = []

    order_items = order.get("order_items", [])
    if not isinstance(order_items, list):
        raise OrderEnrichmentError("Order contains invalid item data.")

    for item in order_items:
        if not isinstance(item, dict):
            raise OrderEnrichmentError("Order contains invalid item data.")
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not item_id.strip():
            raise OrderEnrichmentError("Order contains invalid item data.")

        item_response = _require_success(fetch_catalogue_item(item_id), "Catalogue")
        item_data = item_response.get("data")
        if not isinstance(item_data, dict):
            raise OrderEnrichmentError("Catalogue service returned invalid item data.")

        item_details = dict(item_data)
        item_details["item_price"] = item.get("item_price")
        item_details["item_quantity"] = item.get("item_quantity")
        enriched_items.append(item_details)

    order_details["order_items"] = enriched_items

    if "venue" in order:
        stored_venue = order["venue"]
        if not isinstance(stored_venue, dict):
            raise OrderEnrichmentError("Order contains invalid venue data.")
        venue_id = stored_venue.get("venue_id")
        if not isinstance(venue_id, str) or not venue_id.strip():
            raise OrderEnrichmentError("Order contains invalid venue data.")

        venue_response = _require_success(fetch_venue(venue_id), "Venue")
        venue_data = venue_response.get("data")
        if not isinstance(venue_data, dict):
            raise OrderEnrichmentError("Venue service returned invalid venue data.")

        venue_details = dict(venue_data)
        venue_details["venue_price"] = stored_venue.get("venue_price")
        venue_details["venue_datetime"] = stored_venue.get("venue_datetime")
        order_details["venue"] = venue_details

    return order_details
