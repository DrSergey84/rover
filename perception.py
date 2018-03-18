import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh_ground=(160, 160, 160), rgb_thresh_obstacle=(60, 60, 60)):
    # Create an array of zeros same xy size as img, but single channel
    thresh = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    terrain_thresh = (img[:,:,0] > rgb_thresh_ground[0]) \
                & (img[:,:,1] > rgb_thresh_ground[1]) \
                & (img[:,:,2] > rgb_thresh_ground[2])

    obstacles_thresh = (img[:,:,0] < rgb_thresh_obstacle[0]) \
                & (img[:,:,1] < rgb_thresh_obstacle[1]) \
                & (img[:,:,2] < rgb_thresh_obstacle[2])
                 
    # The rocks are yellow (#FFFF00), or almost yellow...
    rocks_thresh = (img[:,:,0] >= 120) \
                & (img[:,:,1] >= 120) \
                & (img[:,:,2] <= 20)

    # Index the array of zeros with the boolean array and set to 1
    thresh[terrain_thresh] = 3
    thresh[obstacles_thresh] = 2
    thresh[rocks_thresh] = 1
    # Return the binary image
    return thresh

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img, val):
    # Identify nonzero pixels
    object_img = np.zeros_like(binary_img)
    object_img[binary_img == val] = 1

    ypos, xpos = object_img.nonzero()
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

# Reverse the pix_to_world transformation
def world_to_pix(x_world, y_world, xpos, ypos, yaw, image_size, scale):
    # Apply translation
    translate_x = (x_world - xpos) * scale
    translate_y = (y_world - ypos) * scale

    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(translate_x, translate_y, yaw)
    # Perform rotation, translation and clipping all at once
    x_pix = np.clip(np.int_(xpix_rot), 0, image_size[0] - 1)
    y_pix = np.clip(np.int_(ypix_rot), 0, image_size[1] - 1)
    # Return the result
    return x_pix, y_pix

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img
    # 1) Define source and destination points for perspective transform
    image = Rover.img
    dst_size = 5 
    bottom_offset = 6
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset], 
                  [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  ])
    # 2) Apply perspective transform
    warped = perspect_transform(image, source, destination)
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    threshed = color_thresh(warped)
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
    Rover.vision_image[(threshed == 3),:] = (0, 0, 255 )
    Rover.vision_image[(threshed == 2),:] = (20, 20, 20)
    Rover.vision_image[(threshed == 1),:] = (255, 255, 0)
    # 5) Convert map image pixel values to rover-centric coords
    xpix_t, ypix_t = rover_coords(threshed , 3) # 3 - terrain 
    xpix_o, ypix_o = rover_coords(threshed , 2) # 2 - obstacle 
    xpix_r, ypix_r = rover_coords(threshed , 1) # 1 - rock
   
    # Record the world position of the sample
    yellow_pix = np.sum(threshed == 1)

    #This is a special state to recover from the sample picking up
    #By some reasons Rover keeps receiving old/obsolete image from the camera
    # for some time after the sample has been picked up
    if ( Rover.the_rock == -1 and yellow_pix == 0 and Rover.vel > 0.2 ):
        Rover.the_rock = 0

    if (Rover.the_rock == 0 and yellow_pix >= 5):
        Rover.the_rock = 1

    # 6) Convert rover-centric pixel values to world coordinates
    xpos, ypos = Rover.pos
    yaw = Rover.yaw
    navigable_x_world, navigable_y_world = pix_to_world(xpix_t, ypix_t, xpos, 
                                ypos, yaw, 
                                Rover.worldmap.shape[0], 10) 
    
    obstacle_x_world, obstacle_y_world = pix_to_world(xpix_o, ypix_o, xpos, 
                                ypos, yaw, 
                                Rover.worldmap.shape[0], 10) 

    rock_x_world, rock_y_world = pix_to_world(xpix_r, ypix_r, xpos, 
                                ypos, yaw, 
                                Rover.worldmap.shape[0], 10) 

    #Get positions that have been visited recently, 
    #and tell the Rover to avoid toing that way
    explored = (Rover.visited_map > 0)
    explored[explored] = 1
    
    #Convert those recently visited points into the rover-centric coordinates
    x_world, y_world = explored.nonzero()
    explored_xpix, explored_ypix = world_to_pix(x_world, y_world,
                                   xpos, ypos, -yaw, image.shape, 10)

    # Take the median among the visible navigatable point timestamps
    # A coarse-grained approach here, not all the (x,y) pairs can be
    # present in both the navigatable area and the explored area maps
    x_int = np.int_(np.intersect1d(explored_xpix, xpix_t))
    y_int = np.int_(np.intersect1d(explored_ypix, ypix_t))
    pair = list([])
    if ( x_int.size > 0 and y_int.size > 0):
      pair = [(i,j) for i in range(x_int.size) for j in range(y_int.size)]

    #Rover won't consider the most recently visited points
    for (i,j) in pair:
       if (i < xpix_t.size and j < ypix_t.size):
         xpix_t[i] = 0
         ypix_t[j] = 0
       
    #Record xpos, ypos as visited by the Rover and record when it was visited last time
    Rover.visited_map[int(xpos), int(ypos)] = Rover.total_time
    # 7) Update Rover worldmap (to be displayed on right side of screen)
    Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
    Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
    Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1
    # 8) Convert rover-centric pixel positions to polar coordinates
    dist, angles = (-1, -1)
    #if there is a rock, move closer to it, otherwise follow terrain's mean
    if (Rover.the_rock != 1):
        dist, angles = to_polar_coords(xpix_t, ypix_t)
    elif (yellow_pix):
        dist, angles = to_polar_coords(xpix_r, ypix_r)
        Rover.prev_angles_to_sample = angles
    else: 
        #Sometimes I don't threshold yellow pixels in the camera, while the sample is there this is the workaround
        angles = Rover.prev_angles_to_sample
    # Update Rover pixel distances and angles
    Rover.nav_dists = dist
    Rover.nav_angles = angles
     
    return Rover
