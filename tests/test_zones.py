import pytest
from vision.zone_manager import ZoneManager

def test_polygon_zone_containment():
    zm = ZoneManager(camera_id="cam-zone-test")
    zm.add_zone(
        zone_id="apparel-1",
        name="Apparel Section",
        polygon_coords=[[100, 100], [400, 100], [400, 400], [100, 400]]
    )

    # Footprint inside zone
    z_in = zm.check_zone_containment((250, 250))
    assert z_in is not None
    assert z_in['name'] == "Apparel Section"

    # Footprint outside zone
    z_out = zm.check_zone_containment((50, 50))
    assert z_out is None
