import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import numpy as np
import cv2
import time

import math

# expresiones regulares
import re

model_path = 'hand_landmarker.task'

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode
detection_result = None

tips_id = [4,8,12,16,20]
landmarks_hist = []
letters_hist = [] # letras con los dedos
dirs_hist = [] # movimiento relativo entre frame y frame de la mano, el más importante

max_hist = 40 # 40 frames en el video

# controlar la palabra a través de los movimientos con estas variables (tam max)
mov_letter_size = 0 
mov_letter = None
max_move_letter_size = 30

# FUNCIÓN PARA ACTUALIZAR EL HISTÓRICO DE LETRAS Y LANDMARKS.
def update_hist(letter,lm):

  global landmarks_hist
  global letters_hist
  global dirs_hist
  global max_hist
  global tips_id

  x = lm[tips_id[1]].x # punta índice eje x
  y = lm[tips_id[1]].y # punta indice eje y

  if len(dirs_hist) == 0:
    dirs_hist.append('-')
  else:
    lm_ant = landmarks_hist[-1]
    x_ant = lm_ant[tips_id[1]].x
    y_ant = lm_ant[tips_id[1]].y

    if x_ant == x:
      dirs_hist.append('-')
    elif x_ant < x:
      dirs_hist.append('D')
    else:
      dirs_hist.append('I')

  letters_hist.append(letter)
  landmarks_hist.append(lm)
  if len(letters_hist) > max_hist:
    letters_hist.pop(0)
    landmarks_hist.pop(0)
    dirs_hist.pop(0)

# FUNCIÓN PARA DIBUJAR LETRAS DINÁMICAS.
def draw_letter_by_size(image, letter, size):
  font = cv2.FONT_HERSHEY_SIMPLEX
  font_size = size
  font_color = (255,255,255)
  font_thickness = 3

  h,w,_ = image.shape
  text_size, _ = cv2.getTextSize(letter, font, font_size, font_thickness)
  text_w, text_h = text_size
  print(h,w,text_w,text_h)
  cv2.putText(image, letter, (int(w/2)-int(text_w/2), int(h/2)+int(text_h/2)), font, font_size, font_color, font_thickness, cv2.LINE_AA)

  return image

# FUNCIÓN PARA DETECTAR LETRAS DINÁMICAS.
def moving_letter(letter, pattern = r'D{5,}I{5,}D{5,}|I{5,}D{5,}I{5,}'):
  
  #comprobar movimiento
  directions = ''.join(dirs_hist)
  directions = re.sub(r'D-D', 'DD', directions)
  directions = re.sub(r'D-I', 'DI', directions)
  directions = re.sub(r'I-I', 'II', directions)
  directions = re.sub(r'I-D', 'ID', directions)
  print(directions)
  matches = re.findall(pattern, directions) # substrings

  # comprobar letra
  letters = ''.join(letters_hist)
  pattern2 = r'('+letter+'){20,}' # entre parentesis significa que buscamos una cadena completa, sin parentesis significa que buscamos una letra. ('+letter+')
  matches2 = re.findall(pattern2, letters)
  if len(matches) and len(matches2):
    return True
  return False

# FUNCIÓN PARA DETECTAR LETRAS ESTÁTICAS.
def detect_letter(info):
    # Umbral para determinar si la letra 'A' está presente
    if check_extended(info,[0, 0, 0, 0, 0]):
        return 'A'
    # Umbral para determinar si la letra 'B' está presente
    if check_extended(info, [0, 1, 1, 1, 1]) and check_angle(info,[None, 0, 0, 0, 0], 0):
        return 'B'
    # Umbral para determinar si la letr 'C' está presente
    if check_extended(info, [1, 1, 1, 1, 1]) and check_angle(info,[0, 30, 30, 30, 30], 15):
        return 'C'
    # Umbral para determinar si la letra 'D' está presente
    if check_extended(info, [1, 1, 0, 1, 1]) and check_angle(info,[60, 80, None, 0, 0], 50):
        return 'D'
    # Umbral para determinar si la letra 'E' está presente
    if check_extended(info, [1, 0, 0, 0, 0]) and check_angle(info,[40, 60, 60, 60, 60], 20):
        return 'E'
    # Umbral para determinar si la letra 'F' está presente
    if check_extended(info, [1, 0, 1, 1, 1]) and check_angle(info, [60, -40, 60, 80, 90], 10):
        return 'F'
    # Umbral para determinar si la letra 'I' está presente
    if check_extended(info, [1, 0, 0, 0, 1]) and check_angle(info, [80, None, None, None, 90], 20):
        return 'I'
    # Umbral para determinar si la letra 'L' está presente
    if check_extended(info, [1, 1, 0, 0, 0]) and check_angle(info, [0, 90, None, None, None], 20):
        return 'L'
    # Umbral para determinar si la letra 'M' está presente
    if check_extended(info, [1, 1, 1, 1, 0]) and check_angle(info, [-100, -80, -90, -100, 0], 50):
        return 'M'
    # Umbral para determinar si la letra 'N' está presente
    if check_extended(info, [1, 1, 1, 0, 0]) and check_angle(info, [-100, -90, -90, None, None], 10):
        return 'N'
    # Umbral para determinar si la letra 'O' está presente
    if check_extended(info, [1, 0, 1, 1, 1]) and check_angle(info, [60, 0, 60, 80, 90], 50):
        return '0'
    # Umbral para determinar si la letra 'P' está presente
    if check_extended(info, [1, 1, 1, 1, 0]) and check_angle(info, [100, 90, 90, 90, None], 10):
        return 'P'
     # Umbral para determinar si la letra 'Q' está presente
    if check_extended(info, [1, 1, 1, 1, 1]) and check_angle(info, [90, 90, 90, 90, 90], 20):
        return 'Q'
    # Umbral para determinar si la letra 'R' está presente
    if check_extended(info, [1, 1, 1, 0, 0]) and check_angle(info, [100, 90, 90, -60, -50], 10):
        return 'R'
    # Umbral para determinar si la letra 'U' está presente
    if check_extended(info, [1, 1, 1, 0, 0]) and check_angle(info, [100, 80, 90, -60, -50], 10):
        return 'U'
    
    # Si no se detecta ninguna letra
    return '-'

# DEVUELVE LA INFORMACIÓN DE LOS DEDOS.
def finger_info(lm):
  global tips_id
  info = []
  for tip in tips_id:
    x1 = lm[tip].x
    y1 = lm[tip].y
    x2 = lm[tip-1].x
    y2 = lm[tip-1].y
    x3 = lm[0].x
    y3 = lm[0].y
    x4 = lm[tip-3].x
    y4 = lm[tip-3].y
    x5 = lm[0].x
    y5 = lm[0].y   

    d1 = math.sqrt((x1-x3)**2 + (y1-y3)**2)
    d2 = math.sqrt((x2-x3)**2 + (y2-y3)**2)
    d3 = math.sqrt((x3-x5)**2 + (y3-y5)**2)
    d4 = math.sqrt((x4-x5)**2 + (y4-y5)**2)

    max_d = max(d1,d2,d3,d4)
    extended = 0
    if max_d == d1:
      extended = 1
    ang = math.atan2(y4-y1, x4-x1)*180/np.pi
    info.append((extended, int(ang)))
  return info

# DIBUJA LA INFORMACIÓN DE LOS DEDOS.
def draw_finger_info(info, lm, image):
  global tips_id
  font = cv2.FONT_HERSHEY_SIMPLEX
  font_size = 0.5
  font_thickness = 1
  margin = 10
  cont = 0
  for e,angl in info:
    # draw the letter
    h,w, _ = image.shape
    x = int(lm[tips_id[cont]].x * w)
    y = int(lm[tips_id[cont]].y * h)-margin
    if e:
      font_color = (0,255,0)
    else:
      font_color = (0,0,255)
    cv2.putText(image, str(angl), (x,y), font, font_size, font_color, font_thickness, cv2.LINE_AA)
    cont += 1
  return image

# FUNCIÓN PARA IMPRIMIR EL ÁNGULO DE LOS DEDOS.
def print_angle(detection_result):
  global tips_id

  for lm in detection_result.hand_landmarks:
    print(math.atan2(lm[tips_id[1]-3].y - lm[tips_id[1]].y, lm[tips_id[1]].x - lm[tips_id[1]-3].x)*180/np.pi)

# FUNCIÓN PARA IMPRIMIR LA DISTANCIA DE LOS DEDOS.
def print_dist(detection_result):
  global tips_id

  for lm in detection_result.hand_landmarks:
    print(math.sqrt((lm[tips_id[1]].x - lm[tips_id[1]-3].x)**2, (lm[tips_id[1]].y - lm[tips_id[1]-3].y)**2))

# FUNCIÓN PARA IMPRIMIR LA POSICIÓN DE LOS DEDOS.
def print_pos(detection_result):
  global tips_id

  for lm in detection_result.hand_landmarks:
    print(lm[tips_id[1]].x, lm[tips_id[1]].y)

# FUNCIÓN PARA OBTENER EL RESULTADO DE LA DETECCIÓN.
def get_result(result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
  global detection_result
  detection_result = result

# FUNCIÓN PARA DIBUJAR EL BOUNDING BOX CON LA LETRA.
def draw_bb_with_letter(image,detection_result,letter):
  
  font = cv2.FONT_HERSHEY_SIMPLEX
  font_size = 3
  font_color = (255,255,255)
  font_thickness = 3

  bb_color = (0,255,0)
  margin = 10
  bb_thickness = 3

  # Loop through the detected hands to visualize.
  hand_landmarks_list = detection_result.hand_landmarks
  for hand_landmarks in hand_landmarks_list:
    
    # Get the top left corner of the detected hand's bounding box.
    height, width, _ = image.shape
    x_coordinates = [landmark.x for landmark in hand_landmarks]
    y_coordinates = [landmark.y for landmark in hand_landmarks]
    min_x = int(min(x_coordinates) * width) - margin
    min_y = int(min(y_coordinates) * height) - margin
    max_x = int(max(x_coordinates) * width) + margin
    max_y = int(max(y_coordinates) * height) + margin

    # Draw a bounding-box
    cv2.rectangle(image, (min_x,min_y),(max_x,max_y),bb_color,bb_thickness)

    # Get the text size
    text_size, _ = cv2.getTextSize(letter, font, font_size, font_thickness)
    text_w, text_h = text_size
    # Draw background filled rectangle
    cv2.rectangle(image, (min_x,min_y), (min_x + text_w, min_y - text_h), bb_color, -1)  
    # Draw the letter
    cv2.putText(image, letter,(min_x, min_y), font, font_size, font_color, font_thickness, cv2.LINE_AA)
  
  return image

# FUNCIÓN PARA COMPROBAR SI LOS DEDOS ESTÁN EXTENDIDOS.
def check_extended(info, p):
  cont = 0
  for e,angl in info:
    if p[cont] is None:
      continue
    if e != p[cont]:
      return False
    cont += 1
  return True

# FUNCIÓN PARA COMPROBAR SI LOS DEDOS ESTÁN EN UN ÁNGULO.
def check_angle(info, p, tol):
  cont = 0
  for e,angl in info:
    if p[cont] is None:
      continue
    if abs(angl-p[cont]) > tol:
      return False
    cont += 1
  return True

# FUNCIÓN PARA DIBUJAR LOS LANDMARKS EN LA IMAGEN.
def draw_landmarks_on_image(rgb_image, detection_result):

  hand_landmarks_list = detection_result.hand_landmarks
  annotated_image = np.copy(rgb_image)

  # Loop through the detected hands to visualize.
  for hand_landmarks in hand_landmarks_list:
 
    # Draw the hand landmarks.
    hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
    hand_landmarks_proto.landmark.extend([
      landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
    ])
    solutions.drawing_utils.draw_landmarks(
      annotated_image,
      hand_landmarks_proto,
      solutions.hands.HAND_CONNECTIONS,
      solutions.drawing_styles.get_default_hand_landmarks_style(),
      solutions.drawing_styles.get_default_hand_connections_style())

  return annotated_image

#--------------------------------------------------------------------------------------------------------------------------

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=get_result)

with HandLandmarker.create_from_options(options) as landmarker:
  cap = cv2.VideoCapture(0)
  while cap.isOpened():
    success, image = cap.read()
    if not success:
      print("Ignoring empty camera frame.")
      continue
    image = cv2.flip(image,1)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
    frame_timestamp_ms = int(time.time() * 1000)
    landmarker.detect_async(mp_image, frame_timestamp_ms)
    if detection_result is not None:
      image = draw_landmarks_on_image(mp_image.numpy_view(), detection_result)
      image = draw_bb_with_letter(image,detection_result,'-')
      if len(detection_result.hand_landmarks) > 0:
        lm = detection_result.hand_landmarks[0]
        info = finger_info(lm)
        # print(info)
        image2 = draw_finger_info(info,lm,image)

        detect_letra = detect_letter(info)
        image = draw_bb_with_letter(image2, detection_result, detect_letra)

        update_hist(detect_letra, lm)

        if mov_letter_size == 0:
          # Ejemplo Hola
          if moving_letter("A"):
            mov_letter = "Hola"
            mov_letter_size = max_move_letter_size
          # Letra dinámica LL
          if moving_letter("L"):
              mov_letter = "LL"
              mov_letter_size = max_move_letter_size
          # Letra dinámica RR
          if moving_letter("R"):
              mov_letter = "RR"
              mov_letter_size = max_move_letter_size    
          # Letra dinámica Ñ
          if moving_letter("N"):
              mov_letter = "ENIE"
              mov_letter_size = max_move_letter_size 
          # Letra dinámica V
          if moving_letter("U"):
              mov_letter = "V"
              mov_letter_size = max_move_letter_size   
          # Letra dinámica W
          if moving_letter("P"):
              mov_letter = "W"
              mov_letter_size = max_move_letter_size   
          # Letra dinámica J
          if moving_letter("I"):
              mov_letter = "J"
              mov_letter_size = max_move_letter_size  
        if mov_letter_size > 0:
          image = draw_letter_by_size(image, mov_letter, mov_letter_size)
          mov_letter_size -= 1

    cv2.imshow('MediaPipe Hands', image)
    if cv2.waitKey(5) & 0xFF == 27:
      break