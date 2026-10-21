// ============================================================
// Reolink Argus 4 Pro Outdoor Mount + Rain Hood
// Designed for Garage48 / Estonia outdoor use
// Camera body approx: 128 x 87 x 80 mm
// Print in PETG or ASA for outdoor weather resistance
// ============================================================

/* [Camera Cradle] */
cradle_width = 140;          // mm - slightly wider than camera
cradle_depth = 90;           // mm
cradle_height = 45;          // mm - how high the cradle walls are
wall_thickness = 4;          // mm
cradle_lip = 8;              // mm - front lip to hold camera

/* [Mount Arm] */
arm_length = 80;             // mm - distance from wall to camera
arm_width = 40;              // mm
arm_thickness = 8;           // mm

/* [Wall Plate] */
wall_plate_width = 80;       // mm
wall_plate_height = 120;     // mm
wall_plate_thickness = 6;    // mm
mount_hole_diameter = 6;     // mm - for M6 screws or expansion bolts
hole_spacing_y = 80;         // mm

/* [Rain Hood] */
hood_overhang = 40;          // mm - how far the hood extends in front
hood_thickness = 3;          // mm
hood_angle = 15;             // degrees - slight downward slope for rain runoff

/* [Hidden] */
$fn = 60;

// ============================================================
// Modules
// ============================================================

module wall_plate() {
    difference() {
        // Main plate
        cube([wall_plate_width, wall_plate_thickness, wall_plate_height], center=false);
        
        // Mounting holes
        translate([wall_plate_width/2, -1, wall_plate_height/2 - hole_spacing_y/2])
            rotate([-90, 0, 0])
            cylinder(h=wall_plate_thickness+2, d=mount_hole_diameter);
            
        translate([wall_plate_width/2, -1, wall_plate_height/2 + hole_spacing_y/2])
            rotate([-90, 0, 0])
            cylinder(h=wall_plate_thickness+2, d=mount_hole_diameter);
    }
}

module arm() {
    // Simple rectangular arm from wall to cradle
    cube([arm_length, arm_width, arm_thickness], center=false);
}

module cradle() {
    difference() {
        // Outer cradle body
        cube([cradle_width, cradle_depth, cradle_height], center=false);
        
        // Inner cavity (camera sits here)
        translate([wall_thickness, wall_thickness, wall_thickness])
            cube([cradle_width - 2*wall_thickness, 
                  cradle_depth - wall_thickness - cradle_lip, 
                  cradle_height + 1], center=false);
        
        // Front opening (camera faces this way)
        translate([wall_thickness, cradle_depth - cradle_lip - 1, wall_thickness])
            cube([cradle_width - 2*wall_thickness, cradle_lip + 2, cradle_height], center=false);
    }
    
    // Front lip to retain camera
    translate([0, cradle_depth - cradle_lip, 0])
        cube([cradle_width, cradle_lip, wall_thickness], center=false);
}

module rain_hood() {
    // Simple angled rain hood above the camera
    hood_length = cradle_width + 20;
    hood_depth = hood_overhang;
    
    rotate([hood_angle, 0, 0])
        cube([hood_length, hood_depth, hood_thickness], center=false);
}

// ============================================================
// Assembly
// ============================================================

// Wall plate (mounted on wall)
wall_plate();

// Arm extending from wall
translate([ (wall_plate_width - arm_width)/2 , wall_plate_thickness, (wall_plate_height - arm_thickness)/2 ])
    arm();

// Cradle at the end of the arm
translate([ 
    (wall_plate_width - cradle_width)/2 , 
    wall_plate_thickness + arm_length - 10, 
    (wall_plate_height - cradle_height)/2 
])
    cradle();

// Rain hood above the cradle
translate([ 
    (wall_plate_width - cradle_width)/2 - 10, 
    wall_plate_thickness + arm_length + cradle_depth - 20, 
    (wall_plate_height + cradle_height)/2 + 5 
])
    rain_hood();
