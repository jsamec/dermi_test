import cv2
import matplotlib.pyplot as plt
import numpy as np

# stores the marker corners based ont the top left corner and the width of the marker
class Code:
    def __init__(self, id, top_left, code_width = 8):
        self.id = id
        self.top_left_corner = top_left

        x, y = top_left
        self.corners = [(x, y), (x + code_width, y), (x, y + code_width), (x + code_width, y + code_width)]    

class ImageProcessor:
    # circle_positions based on code 18 top left corner in mm
    CIRCLE_POSITIONS = {
        1: (13.5, 3),
        2: (21, 3),
        3: (29, 3),   
        4: (36.5, 3),
        5: (13.5, 11.5),
        6: (21, 11.5),
        7: (29, 11.5),   
        8: (36.5, 11.5),
        9: (4.5, 12.5),
        10: (4.5, 21),
        11: (4.5, 29.5),
        12: (4.5, 38),
        13: (4.5, 46),
        14: (4.5, 54.5),
        15: (13.5, 54.5),
        16: (21, 54.5),
        17: (29, 54.5),   
        18: (36.5, 54.5),
        19: (45.5, 54.5),
        20: (45.5, 46),
        21: (45.5, 38),
        22: (45.5, 29.5),
        23: (45.5, 21),
        24: (45.5, 12.5),
    }

    ACTUAL_RGB_VALUES = {
        1: (154, 144, 138),
        2: (103, 91, 88),
        3: (194, 164, 135),
        4: (106, 88, 77),
        5: (179, 131, 127),
        6: (194, 126, 111),
        7: (166, 139, 110),
        8: (194, 122, 116),
        9: (166, 97, 93),
        10: (133, 111, 121),
        11: (193, 171, 160),
        12: (129, 114, 101),
        13: (133, 111, 118),
        14: (167, 96, 101),
        15: (173, 91, 120),
        16: (75, 66, 71),
        17: (163, 138, 131),
        18: (192, 166, 170),
        19: (102, 91, 78),
        20: (196, 122, 136),
        21: (176, 130, 119),
        22: (194, 165, 133),
        23: (90, 56, 68),
        24: (188, 165, 173)
    }

    ACTUAL_CIELAB_VALUES = {
        1: (60, 2.5, 4.33012701892219),
        2: (40, 3.83022221559489, 3.2139380484327),
        3: (70, 6.84040286651337, 18.7938524157182),
        4: (40, 5.0, 8.66025403784439),
        5: (60, 17.3205080756888, 10.0),
        6: (60, 22.9813332935693, 19.2836282905962),
        7: (60, 5.17638090205042, 19.3185165257814),
        8: (60, 25.9807621135332, 15.0),
        9: (50, 25.9807621135332, 15.0),
        10: (50, 9.84807753012208, -1.7364817766693),
        11: (70, 6.42787609686539, 7.66044443118978),
        12: (50, 3.42020143325669, 9.39692620785909),
        13: (50, 10, 0),
        14: (50, 28.1907786235773, 10.2606042997701),
        15: (50, 35, 0),
        16: (30, 4.69846310392954, -1.71010071662834),
        17: (60, 7.66044443118978, 6.42787609686539),
        18: (70, 9.84807753012208, 1.7364817766693),
        19: (40, 2.58819045102521, 9.65925826289068),
        20: (60, 29.5442325903662, 5.20944533000791),
        21: (60, 15.3208888623796, 12.8557521937308),
        22: (70, 5.17638090205042, 19.3185165257814),
        23: (30, 15, 0),
        24: (70, 9.84807753012208, -1.7364817766693)
    }

    WIDTH_OF_CARD = 50 #mm
    HEIGHT_OF_CARD = 74 #mm
    SCALING_FACTOR = 15

    WIDTH_OFFSET = WIDTH_OF_CARD * SCALING_FACTOR
    HEIGHT_OFFSET = HEIGHT_OF_CARD * SCALING_FACTOR

    CODE_WIDTH = 8

    CODE_POSITIONS = {
        18: Code(18, (0, 0), CODE_WIDTH),
        14: Code(14, (WIDTH_OF_CARD - CODE_WIDTH, 0), CODE_WIDTH),
        2: Code( 2, (0, HEIGHT_OF_CARD - CODE_WIDTH), CODE_WIDTH),
        16: Code(16, (WIDTH_OF_CARD - CODE_WIDTH, HEIGHT_OF_CARD - CODE_WIDTH), CODE_WIDTH)
    }

    WINDOW_SHAPE = [15, 19, 36, 45]

    EDGES_MIN = 20
    EDGES_MAX = 40
    THRESH = 90
    THRESH_MAX = 210

    code_type_to_detect = cv2.aruco.DICT_4X4_50
    aruco_code_dictionary = cv2.aruco.Dictionary_get(code_type_to_detect)
    aruco_code_parameters = cv2.aruco.DetectorParameters_create()

    detected_corners = []
    original_corners = []

    circle_median_colors = {}

    def start(self, image):
        self.clear_data()

        # deskew the image using markers and homography
        corrected_image = self.correct_image(image)
        corrected_image = cv2.GaussianBlur(corrected_image, (5, 5), 0)

        # mark the circles and the skin window
        corrected_image_with_markers = corrected_image.copy()
        corrected_image_with_markers = self.mark_image(corrected_image_with_markers) # this function is not needed for the color correction, it is only used for visualization

        # crop the skin window
        skin_window = corrected_image[int(self.WINDOW_SHAPE[1] * self.SCALING_FACTOR):int(self.WINDOW_SHAPE[3] * self.SCALING_FACTOR), 
                                      int(self.WINDOW_SHAPE[0] * self.SCALING_FACTOR):int(self.WINDOW_SHAPE[2] * self.SCALING_FACTOR)]
    
        # calculate the coefficients for color correction
        coefficients = self.get_normalization_matrix(self.circle_median_colors, self.ACTUAL_RGB_VALUES)
        coefficients_CIELAB = self.get_normalization_matrix(self.circle_median_colors, self.ACTUAL_CIELAB_VALUES)
        
        # apply color correction
        color_correction_function = lambda k, x : k[0]*x[0] + k[1]*x[1] + k[2]*x[2] + k[3]

        b, g, r = cv2.split(skin_window)
        norm_r = color_correction_function(coefficients[0],(r,g,b))
        norm_g = color_correction_function(coefficients[1],(r,g,b))
        norm_b = color_correction_function(coefficients[2],(r,g,b))
        skin_window_corrected = cv2.merge([norm_r, norm_g, norm_b])
        skin_window_corrected_float = cv2.merge([norm_r, norm_g, norm_b])       
        skin_window_corrected = np.uint8(skin_window_corrected) # convert to uint8 for visualization/procesing

        # display the results
        #_, ax = plt.subplots(1, 4, figsize=(20, 10))
        #ax[0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        #ax[1].imshow(cv2.cvtColor(corrected_image_with_markers, cv2.COLOR_BGR2RGB))
        #ax[2].imshow(skin_window_corrected)     

        # black out hairs and pigment
        clear_skin_window, hair_mask, pigment_mask = self.remove_hair_and_pigment(skin_window_corrected)
      
        # extract the non black pixels for the float version of the image
        clear_skin_window_float = cv2.bitwise_and(skin_window_corrected_float, skin_window_corrected_float, mask=pigment_mask)
        clear_skin_window_float = cv2.bitwise_and(clear_skin_window_float, clear_skin_window_float, mask=hair_mask)
        skin_pixels_float = clear_skin_window_float[np.all(clear_skin_window_float != [0, 0, 0], axis=2)]
        self.skin_pixels_float = skin_pixels_float / 255  

        #ax[3].imshow(clear_skin_window)        

        self.clear_skin = clear_skin_window.copy()                 

        # extract the non black pixels
        skin_pixels = clear_skin_window[np.all(clear_skin_window != [0, 0, 0], axis=2)]
        self.skin_pixels = skin_pixels

        # calculate the median pixel
        median_pixel = np.median(skin_pixels, axis=0)

        # calculate the corrected median pixel and EI
        self.corrected_median_pixel = [color_correction_function(coefficients[0], median_pixel), 
                                       color_correction_function(coefficients[1], median_pixel), 
                                       color_correction_function(coefficients[2], median_pixel)]
        self.corrected_median_pixel_CIELAB = [color_correction_function(coefficients_CIELAB[0], median_pixel), 
                                              color_correction_function(coefficients_CIELAB[1], median_pixel), 
                                              color_correction_function(coefficients_CIELAB[2], median_pixel)]
        self.EI = np.sqrt(self.corrected_median_pixel[0] * self.corrected_median_pixel[2])/self.corrected_median_pixel[1]

        #print("Corrected median pixel: " + str(self.corrected_median_pixel))
        #print("Corrected median pixel CIELAB: " + str(self.corrected_median_pixel_CIELAB))
        #print("EI: " + str(self.EI))

        #plt.show()
        #plt.pause(0.001)

    def remove_hair_and_pigment(self, skin_window_corrected):
        # remove hairs by using canny edge detection and then eroding the image
        gray_cropped_image = cv2.cvtColor(skin_window_corrected, cv2.COLOR_BGR2GRAY)
        robovi = cv2.Canny(gray_cropped_image, self.EDGES_MIN, self.EDGES_MAX)
        robovi = cv2.bitwise_not(robovi)
        robovi = cv2.erode(robovi, np.ones((3,3), np.uint8), iterations=2)
        _, hair_mask = cv2.threshold(gray_cropped_image, self.THRESH_MAX, 255, cv2.THRESH_BINARY_INV)
        hair_mask = cv2.bitwise_and(robovi, hair_mask)
        skin_window_corrected_clean = cv2.bitwise_and(skin_window_corrected, skin_window_corrected, mask=hair_mask)

        # remove pigment by using thresholding and then eroding the image
        _, pigment_mask = cv2.threshold(gray_cropped_image, self.THRESH, 255, cv2.THRESH_BINARY)
        pigment_mask = cv2.erode(pigment_mask, np.ones((3,3), np.uint8), iterations=3)

        skin_window_corrected_clean = cv2.bitwise_and(skin_window_corrected_clean, skin_window_corrected_clean, mask=pigment_mask)

        return skin_window_corrected_clean, hair_mask, pigment_mask

    def close(self):
        plt.close()

    def save(self, name): 
        plt.savefig(name)
        plt.close()

        # write EI, correct_median_pixel, corrected_median_pixel_CIELAB to file
        name_without_extension = name.split(".")[0]
        f = open(name_without_extension + ".txt", "w")
        f.write("EI: " + str(self.EI) + "\n")
        f.write("Corrected median pixel: " + str(self.corrected_median_pixel) + "\n")
        f.write("Corrected median pixel CIELAB: " + str(self.corrected_median_pixel_CIELAB) + "\n")
        
        # write skin pixels to file, limit the number of pixels to 100000 (should be around 5MB)
        for i in range(0, min(len(self.skin_pixels_float), 100000), 1):
            f.write(str(self.skin_pixels_float[i][0]) + " " + str(self.skin_pixels_float[i][1]) + " " + str(self.skin_pixels_float[i][2]) + "\n")
        
        f.close()
        
    def euclidean_distance(self, point_1, point_2):
        return np.sqrt(((point_1[0] - point_2[0]) ** 2) + ((point_1[1] - point_2[1]) ** 2))

    def detect_markers(self, image):
        # we detect the markers on multiple images (BGR/RGB, grayscale, different thresholds)
        # we then use the result with the most detected markers
        # RGB image might only detect 2 out of the 4 markers, but the grayscale image might detect all 4

        # detect markers on the original image
        number_of_detected_markers = 0
        (corners, ids, _) = cv2.aruco.detectMarkers(image, self.aruco_code_dictionary, parameters=self.aruco_code_parameters)
        number_of_detected_markers = len(corners)

        # detect markers on the grayscale image
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        (potential_corners, potential_ids, _) = cv2.aruco.detectMarkers(grayscale, self.aruco_code_dictionary, parameters=self.aruco_code_parameters)

        # if we detect more markers on the grayscale image, we use that result
        if len(potential_corners) > number_of_detected_markers:
            number_of_detected_markers = len(potential_corners)
            corners = potential_corners
            ids = potential_ids

        # detect markers on the grayscale image with different thresholds
        for threshold in range(50, 170, 10):
            _, thres = cv2.threshold(grayscale, threshold, 255, cv2.THRESH_BINARY)

            (potential_corners, potential_ids, _) = cv2.aruco.detectMarkers(thres, self.aruco_code_dictionary, parameters=self.aruco_code_parameters)

            # if we detect more markers on the grayscale/RGB image, we use that result
            if len(potential_corners) > number_of_detected_markers:
                number_of_detected_markers = len(potential_corners)
                corners = potential_corners
                ids = potential_ids

        #print("Number of detected markers: {}".format(number_of_detected_markers))
        return (corners, ids)

    def clear_data(self):
        self.detected_corners = []
        self.original_corners = []
        self.corrected_median_pixel = []
        self.corrected_median_pixel_CIELAB = []
        self.clear_skin = None
        self.skin_pixels = None
        self.EI = 0
        self.skin_pixels_float = None

    def correct_image(self, image):
        (corners, ids) = self.detect_markers(image)

        # check if we detected any markers
        if len(corners) > 0:

            # use the markers to calculate the homography matrix
            # from each marker we take each corner and use it for homography estimation
            # the homography can be done using only one marker, but the more markers we use, the more accurate the result will be

            ids = ids.flatten()

            for (marker_id, marker_corner) in sorted(zip(ids, corners), key=lambda pair: pair[0]):

                # sometimes we falsely detect a marker, so we check if the marker is in the CODE_POSITIONS dictionary    
                if marker_id not in self.CODE_POSITIONS:
                    #print("Marker with id {} is not in the CODE_POSITIONS dictionary".format(marker_id))
                    continue

                # save the marker corners
                corners = marker_corner.reshape((4, 2))
                (top_left, top_right, bottom_right, bottom_left) = corners
                corners = (top_left, top_right, bottom_left, bottom_right)
                for i, corner in enumerate(corners):
                    self.detected_corners.append(corner)
                    self.original_corners.append(self.CODE_POSITIONS[marker_id].corners[i])
        else:
            raise Exception("No markers detected")

        # calculate the homography matrix
        h, w = image.shape[:2]
        H, _ = cv2.findHomography(np.array(self.detected_corners), np.array(self.original_corners) * self.SCALING_FACTOR, method=cv2.RANSAC, ransacReprojThreshold=10.0)

        # deskew the image using the homography matrix
        corrected_image = cv2.warpPerspective(image, H, (w, h), flags=cv2.INTER_LINEAR)
        corrected_image = corrected_image[0:self.HEIGHT_OFFSET, 0:self.WIDTH_OFFSET]

        self.clear_data()

        return corrected_image

    def mark_image(self, image):

        for circle in self.CIRCLE_POSITIONS:
            mask = np.zeros(image.shape, dtype=np.uint8)
            mask = cv2.circle(mask, (int(self.CIRCLE_POSITIONS[circle][0] * self.SCALING_FACTOR), int(self.CIRCLE_POSITIONS[circle][1] * self.SCALING_FACTOR)), int(self.SCALING_FACTOR * 1.5), (255, 255, 255), -1)

            masked_image = cv2.bitwise_and(image, image , mask=mask[:,:,0])
            masked_image = masked_image[np.all(masked_image != [0, 0, 0], axis=-1)]
            median_color = [np.median(masked_image[:, 2]), np.median(masked_image[:, 1]), np.median(masked_image[:, 0])]
            self.circle_median_colors[circle] = median_color

            cv2.circle(image, (int(self.CIRCLE_POSITIONS[circle][0] * self.SCALING_FACTOR), int(self.CIRCLE_POSITIONS[circle][1] * self.SCALING_FACTOR)), int(self.SCALING_FACTOR * 1.5), median_color[::-1], -1)
            cv2.circle(image, (int(self.CIRCLE_POSITIONS[circle][0] * self.SCALING_FACTOR), int(self.CIRCLE_POSITIONS[circle][1] * self.SCALING_FACTOR)), int(self.SCALING_FACTOR * 1.5), (0, 0, 255), 1)
            
            cv2.putText(image, str(circle), (int(self.CIRCLE_POSITIONS[circle][0] * self.SCALING_FACTOR), int(self.CIRCLE_POSITIONS[circle][1] * self.SCALING_FACTOR)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        cv2.rectangle(image, (int(self.WINDOW_SHAPE[0] * self.SCALING_FACTOR), int(self.WINDOW_SHAPE[1] * self.SCALING_FACTOR)), (int(self.WINDOW_SHAPE[2] * self.SCALING_FACTOR), int(self.WINDOW_SHAPE[3] * self.SCALING_FACTOR)), (0, 255, 0), 3)

        return image

    def get_normalization_matrix(self, measured_RGB_values, actual_values):
        #model = R*k2 + G*k3 + B*k4 + k1
        # this can be calculated using least squares method, other methods are also possible

        number_of_patches = measured_RGB_values.keys().__len__()
        A = np.ones((number_of_patches, 4))
        B = np.ones((number_of_patches, 3)) 

        for color_id in measured_RGB_values.keys():
            color = measured_RGB_values[color_id]
            A[color_id - 1, 0:3] = color
            color = actual_values[color_id]
            B[color_id - 1, 0:3] = color

        all_coefficients = []
        for i in range(0, 3):
            coefficients = np.linalg.lstsq(A, B[:, i], rcond=None)[0]
            all_coefficients.append(coefficients)

        return all_coefficients

if __name__ == "__main__":
    c = ImageProcessor()

    image_name = "./slike_kalibra/S1.jpg"
    image = cv2.imread(image_name)
    
    c.start(image)
