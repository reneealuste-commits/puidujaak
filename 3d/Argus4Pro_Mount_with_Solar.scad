// ============================================================
// Improved Argus 4 Pro Mount + Rain Hood + Solar Panel Bracket
// Parametric - open in OpenSCAD, adjust, export STL
// ============================================================

/* [Camera] */
camera_width = 128;
camera_depth = 80;
cradle_clearance = 4;

/* [Mount] */
arm_length = 90;
wall_plate_w = 90;
wall_plate_h = 140;

/* [Solar Bracket] */
solar_bracket = true;
solar_panel_width = 180;   // approx Reolink Solar Panel 2
solar_tilt = 65;           // degrees - steep for Estonia winter

/* [Hidden] */
$fn = 48;
wt = 4; // wall thickness

module wall_plate() {
    difference() {
        cube([wall_plate_w, 8, wall_plate_h]);
        translate([wall_plate_w/2, -1, 30])
            rotate([-90,0,0]) cylinder(h=10, d=6.5);
        translate([wall_plate_w/2, -1, wall_plate_h-30])
            rotate([-90,0,0]) cylinder(h=10, d=6.5);
    }
}

module arm() {
    cube([arm_length, 35, 10]);
}

module cradle() {
    outer_w = camera_width + 2*cradle_clearance + 2*wt;
    outer_d = camera_depth + cradle_clearance + wt;
    difference() {
        cube([outer_w, outer_d, 50]);
        translate([wt, wt, wt])
            cube([outer_w-2*wt, outer_d-wt-6, 55]);
    }
    // front lip
    translate([0, outer_d-6, 0])
        cube([outer_w, 6, wt]);
}

module solar_bracket() {
    if (solar_bracket) {
        // Simple angled plate for solar panel
        rotate([solar_tilt, 0, 0])
            cube([solar_panel_width, 8, 120]);
    }
}

// Assembly
wall_plate();

translate([(wall_plate_w-35)/2, 8, (wall_plate_h-10)/2])
    arm();

translate([(wall_plate_w - (camera_width+2*cradle_clearance+2*wt))/2,
           8+arm_length-15,
           (wall_plate_h-50)/2])
    cradle();

// Solar bracket mounted above/behind
translate([wall_plate_w/2 - solar_panel_width/2, 8, wall_plate_h - 20])
    solar_bracket();
