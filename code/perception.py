import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))
                            
    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped

# Define a function to find rock pixels given an image
def find_rocks(img, rgb_thresh=(110, 110, 50)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] < rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img
    # Set necessary paramaters
    dst_size = 5
    scale = 2 * dst_size
    xpos = Rover.pos[0]
    ypos = Rover.pos[1]
    yaw = Rover.yaw
    world_size = Rover.worldmap.shape[0]

    image = Rover.img
    bottom_offset = 6

    # 1) Define source and destination points for perspective transform
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset], 
                  [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  ])
    # 2) Apply perspective transform
        # 2a) apply perspective transform on source image
    warped = perspect_transform(image, source, destination)
        # 2b) apply perspective transform on camera view to create a mask to find obstacles.
    camera_view_mask = perspect_transform(np.ones_like(image[:,:,0]), source, destination)
    

    # 3) Apply color threshold to identify navigable terrain/obstacles
    rgb_thresh = (160,160,160)
    threshed_navigable = color_thresh(warped,rgb_thresh=rgb_thresh)
    threshed_obstacles = -camera_view_mask * (threshed_navigable - 1)


    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
    Rover.vision_image[:,:,2] = threshed_navigable * 255
    Rover.vision_image[:,:,0] = threshed_obstacles * 255

        # Example: Rover.vision_image[:,:,0] = obstacle color-thresholded binary image
        #          Rover.vision_image[:,:,2] = navigable terrain color-thresholded binary image

    # 5) Convert map image pixel values to rover-centric coords
    x_pix_rover_navigable, y_pix_rover_navigable = rover_coords(threshed_navigable)
    x_pix_rover_obstacles, y_pix_rover_obstacles = rover_coords(threshed_obstacles)
    
    # 6) Convert rover-centric pixel values to world coordinates
    world_pix_navigable_x, world_pix_navigable_y = pix_to_world(x_pix_rover_navigable, y_pix_rover_navigable, xpos, ypos, yaw, world_size, scale)
    world_pix_obstacles_x, world_pix_obstacles_y = pix_to_world(x_pix_rover_obstacles, y_pix_rover_obstacles, xpos, ypos, yaw, world_size, scale)

    # 7) Update Rover worldmap (to be displayed on right side of screen)
    
    if Rover.vel > 0.2 and Rover.brake == 0.0:
        # Giver higher weight to pixel classified as navigable terrain.
        Rover.worldmap[world_pix_obstacles_y, world_pix_obstacles_x, 0] += 1
        Rover.worldmap[world_pix_navigable_y, world_pix_navigable_x, 2] += 10
        # Example: Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        #          Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
        #          Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1

    # 8) Convert rover-centric pixel positions to polar coordinates
    rover_centric_pixel_distances, rover_centric_angles = to_polar_coords(x_pix_rover_navigable, y_pix_rover_navigable)
    # Update Rover pixel distances and angles
    Rover.nav_dists = rover_centric_pixel_distances
    Rover.nav_angles = rover_centric_angles
    # 9) Do the same for rock samples
    threshed_rock = find_rocks(warped) 

    
    # If a rock is on the image convert the pixels of the rock to world coordinates.
    if threshed_rock.any():
        x_pix_rover_rock, y_pix_rover_rock = rover_coords(threshed_rock)
        world_pix_rock_x, world_pix_rock_y = pix_to_world(x_pix_rover_rock, y_pix_rover_rock, xpos, ypos, yaw, world_size, scale)
        
        Rover.worldmap[world_pix_rock_x,world_pix_rock_y,:] = 255


        rock_dist, rock_ang = to_polar_coords(x_pix_rover_rock, y_pix_rover_rock)
        rock_idx = np.argmin(rock_dist)
        rock_xcen = world_pix_rock_x[rock_idx]
        rock_ycen = world_pix_rock_y[rock_idx]

        Rover.worldmap[rock_ycen, rock_xcen, 1] = 255

        Rover.rock_dist = rock_dist[rock_idx]
        Rover.rock_ang = rock_ang
    else:
        Rover.rock_dist = None
        

    Rover.vision_image[:,:,1] = threshed_rock * 255



    
 
    
    
    return Rover