import numpy as np

# Make a decision about the steering angle here
def calculate_steer(Rover):
    # most recently visited points
    terrain_angle = np.mean(Rover.nav_angles)
    angle = np.clip(terrain_angle* 180/np.pi, -15, +15)
    return angle


# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

    # Example:
    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward': 
            # Check the extent of navigable terrain
            if len(Rover.nav_angles) >= Rover.stop_forward:  
                # If near sample keep minimum speed 
                if (Rover.near_sample):
                    if (Rover.vel <= 0.2):
                        Rover.throttle = Rover.throttle_set
                    else:
                        Rover.throttle = 0
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                elif Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                # round up the location state
                pos = (int(round(Rover.pos[0])), int(round(Rover.pos[1])))
		# Move towards the average direction of the terrain and opposite from the
                # most recently visited points
                angle = calculate_steer(Rover)
                #print(explore_angle, terrain_angle, angle)

                # we have probably got stuck, move opposite way
                if (Rover.stuck_control[pos]  > 50):
                    Rover.mode = 'stuck'
                 
                Rover.steer = np.clip(angle, -15, 15)
                # record the skiding position
                if (Rover.vel < 0.2):
                    Rover.stuck_control[ pos ] += 1

                # Reduce the speed to not miss the rock
                if (Rover.the_rock == 1):
                    Rover.stuck_control[:,:] = 0
                    Rover.mode = 'near_sample'
                    Rover.throttle = 0

            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                # Set mode to "stop" and hit the brakes!
                Rover.throttle = 0
                # Set brake to stored brake value
                Rover.brake = Rover.brake_set
                Rover.steer = 0
                # Reduce the speed to not miss the rock
                # the samples are normaly located near the mountains which
                # can easily hit this stop_forward condition
                if (Rover.the_rock == 1):
                    Rover.stuck_control[:,:] = 0
                    Rover.mode = 'near_sample'
                else:
                    Rover.mode = 'stop'

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Set steer to mean angle
                    Rover.mode = 'forward'

                    # Release the brake
                    Rover.brake = 0
        elif Rover.mode == 'stuck':
             pos = (int(round(Rover.pos[0])), int(round(Rover.pos[1])))
             # Quite silly algorithms trying to continuously pull into the corners as hard as possible
             # (lef,right,forward, backward), Pulls each direction for 200 frames in a row until some
             # velocity is gained.
             if Rover.vel < -0.4 or Rover.vel > 0.4:
                 Rover.mode = 'forward'
                 Rover.throttle = Rover.throttle_set
                 Rover.stuck_control[:,:] = 0
             elif (Rover.stuck_control[pos]  < 200):
                 Rover.throttle = - 1
                 Rover.steer = 15
             elif (Rover.stuck_control[pos] < 400):
                 Rover.throttle = 1
                 Rover.steer = -15
             elif (Rover.stuck_control[pos] < 600):
                 Rover.throttle = 1
                 Rover.steer = 15
             elif (Rover.stuck_control[pos] < 800):
                 Rover.throttle = -1
                 Rover.steer = -15
             elif (Rover.stuck_control[pos] < 1000):
                 Rover.throttle = -1
                 Rover.steer = 0
             elif (Rover.stuck_control[pos] < 1200):
                 Rover.throttle = 1
                 Rover.steer = 0
             else:
                 Rover.stuck_control[pos] = 0;

             Rover.stuck_control[pos] += 1
        #Try to pick up the sample
        elif Rover.mode == 'near_sample':
            # Reduce the speed
            if Rover.vel > 0.4 or Rover.near_sample:
                Rover.throttle = 0
                Rover.brake = 1

            elif (Rover.the_rock == 1):
                Rover.brake = 0
                # Set steering
		# Move towards the average direction of the terrain and opposite from the
                # most recently visited points
                Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                # TODO: This can be done better by controlling the distance to the rock sample
                Rover.throttle = 0.1
            #The rock is not visible anymore or has been picked up
            else:
                Rover.mode = 'forward'
                Rover.brake = 0
                Rover.throttle = Rover.throttle_set
 
    # Just to make the rover do something 
    # even if no modifications have been made to the code
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
        Rover.the_rock = -1
    
    return Rover

