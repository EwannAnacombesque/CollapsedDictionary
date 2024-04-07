import pygame 
import pygame.gfxdraw
import math
import random
import wfca
import json 
import threading

#=- Alphabetically ordered helper functions -=#

def add_vec(vec1,vec2):
    return [ai + vec2[i] for i,ai in enumerate(vec1)]

def int_vec(vec):
    return [int(v) for v in vec]

def generate_elipsoid(position,angle,radius,harmonics,tick):
    excentricity = 1+ generate_excentricity(angle,harmonics,tick)
    x = position[0]+math.cos(angle)*radius*excentricity
    y = position[1]+math.sin(angle)*radius*excentricity
    return [x,y]

def generate_excentricity(angle,harmonics,tick):
    return sum([harmonic[1]*math.cos(harmonic[3]+tick/harmonic[2] + harmonic[0]*angle) for harmonic in harmonics])

def get_mouse_angle(position):
    return math.atan2(-(position[1]-pygame.mouse.get_pos()[1]),-(position[0]-pygame.mouse.get_pos()[0]))

def get_mouse_distance(position):
    mouse_pos = pygame.mouse.get_pos()
    return math.sqrt((position[0]-mouse_pos[0])**2 + (position[1]-mouse_pos[1])**2)

def process_letter(text,letter,searching):
    allowed_letters = "abcdefghijklmnopqrstuvwxyzéèê’ç"

    
    if searching == "gapped": allowed_letters+= "_"

    if letter == "backspace":
        return text[:-1]
    
    if letter == "space" and text.replace(" ",""):
        return text + " "
    
    letter = letter.replace("2","é").replace("7","è").replace("^","ê").replace("8","_").replace("4","’").replace("9","ç")

    if letter not in allowed_letters:
        return text 

    return text + letter

def to_rect(x,y,w,h,inted=True):
    if inted:
        return [int_vec([x+w/2,y+h/2]),int_vec([x+w/2,y-h/2]),int_vec([x-w/2,y-h/2]),int_vec([x-w/2,y+h/2])]
    return [[x+w/2,y+h/2],[x+w/2,y-h/2],[x-w/2,y-h/2],[x-w/2,y+h/2]]

#=- API and Slide -=#

class API():
    def __init__(self):
        #=- Pygame set up -=#
        #===================#
        self.screen_width = 1300
        self.screen_heigth = int(self.screen_width*9/16)
        
        self.screen = pygame.display.set_mode(( self.screen_width, self.screen_heigth),pygame.RESIZABLE)
        pygame.display.set_caption("A collapsed dictionary")

        self.running = True 
        self.clock = pygame.time.Clock()
        self.tick = 0
        self.floated_tick = 0
        pygame.init()
        
        #=- WFCA set up -=#
        #=================#
        
        self.corpora = ["Texts/FrenchCorpus.txt","Texts/EnglishCorpus.txt","Texts/LatinCorpus.txt","Texts/SpanishCorpus.txt","Texts/PoemCorpus.txt"]
        self.corpora_names = ["French","English","Latin","Spanish","Poem"]
        self.word_ends = ["er","ed","us","ar","t"]
        self.word_end_index = 0
        self.text_index = 0
        
        self.collapsed_text = wfca.CollapsedText()
        
        #=- UX set up -=#
        #===============#
        
        self.main_color = (18,22,25)
        self.background_color = (234,222,218)
        self.fonts = [pygame.font.Font("mirage.otf",int(self.screen_width/12)),pygame.font.Font("mirage.otf",int(self.screen_width/30)),pygame.font.Font("mirage.otf",int(self.screen_width/10))]
        self.addons = [self.background_color,self.main_color,self.fonts,self.screen_width]

        self.requests = {"change slide":[],"change language":[],"change_words":[],"applying_changes":False}
        self.submits = {"key_pressed":[]}
        
        # Create the slides

        self.slides = {"main":Slide("main",*self.addons),
                       "dictionary":Slide("dictionary",*self.addons),
                       "completion":Slide("completion",*self.addons),
                       "parameters":Slide("parameters",*self.addons)}
        
        self.current_slide = self.slides["main"]

    def run(self):
        while self.running:
            self.event()
            self.update()
            self.draw()
    
    def event(self):
        self.submits =  {"key_pressed":[]}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:                    
                self.submits["key_pressed"].append(pygame.key.name(event.key))
    
    def draw(self):
        
        self.current_slide.draw(self.screen,self.tick)

        pygame.display.flip()

    def process_requests(self):
        if self.requests["change slide"]:
            if self.requests["change slide"][0] not in list(self.slides.keys()): return 
            self.current_slide = self.slides[self.requests["change slide"][0]]
        
        if self.requests["change spaced"]:
            
            x = threading.Thread(target=self.generate_threaded_spaced_words,group=None,daemon=True)
            x.start()
            
        if self.requests["change gapped"]:
            
            x = threading.Thread(target=self.generate_threaded_gapped_words,group=None,daemon=True)
            x.start()
            
        if self.requests["change language"]:
            self.text_index = (self.text_index+1)%len(self.corpora)
            self.slides["parameters"].elements["button texts"][0].base_text = self.corpora_names[self.text_index]
            self.slides["parameters"].elements["button texts"][0].render_text()
        
        if self.requests["change word end"]:
            self.word_end_index = (self.word_end_index+1)%len(self.word_ends)
            self.slides["parameters"].elements["button texts"][1].base_text = "End in -"+self.word_ends[self.word_end_index]
            self.slides["parameters"].elements["button texts"][1].render_text()
            
    def generate_threaded_spaced_words(self):
        generated_words = self.words_call(self.requests["change spaced"][0],self.corpora[self.text_index],False)
        for i in range(min(16,len(generated_words))):
            self.current_slide.elements["button texts"][i].base_text = generated_words[i]
            self.current_slide.elements["button texts"][i].current_text = self.current_slide.elements["button texts"][i].base_text
            self.current_slide.elements["button texts"][i].current_color = self.current_slide.elements["button texts"][i].main_color
            self.current_slide.elements["button texts"][i].base_text_rendered = self.current_slide.elements["button texts"][i].update_rendered_text()

    def generate_threaded_gapped_words(self):
        generated_words = self.words_call(self.requests["change gapped"][0],self.corpora[self.text_index],True)
        for i in range(min(10,len(generated_words))):
            self.current_slide.elements["button texts"][i].base_text = generated_words[i]
            self.current_slide.elements["button texts"][i].current_text = self.current_slide.elements["button texts"][i].base_text
            self.current_slide.elements["button texts"][i].current_color = self.current_slide.elements["button texts"][i].main_color
            self.current_slide.elements["button texts"][i].base_text_rendered = self.current_slide.elements["button texts"][i].update_rendered_text()

    def words_call(self,seed,text,gapped):
        generated_words = []
        current_word_end = self.word_ends[self.word_end_index]
        
        if gapped:
            generated_words += self.collapsed_text.generate_gapped_text(200,text,seed)
            generated_words = list(set(generated_words))
            generated_words.sort()
            return generated_words
        
        
        if len(seed) == 0:
            length = 4
        else:
            length = 2
        
        
        generated_words += self.collapsed_text.generate_spaced_text(200,text,seed,current_word_end+"!",length)
        generated_words = list(set(generated_words))
        generated_words.sort()
        return generated_words

    def update(self):
        self.clock.tick(90)
        self.requests = {"change slide":[],"change language":[],"change word end":[],"change spaced":[],"change gapped":[],"applying_changes":False}
        
        self.current_slide.update(self.requests,self.submits)
        self.process_requests()


        self.floated_tick +=0.666
        self.tick = int(self.floated_tick)

class Slide():
    def __init__(self,identifiant,background_color,main_color,fonts,screen_width):
        # Get data from API
        self.background_color = background_color
        self.main_color = main_color
        self.altered_color = (120,100,82)
        self.fonts = fonts
        self.identifiant = identifiant
        self.screen_width = screen_width

        self.addons = {"fonts":fonts,
                       "colors":{"main color":self.main_color,"background color":self.background_color,"altered color":self.altered_color,"desaltered color":(134,98,110)},
                       "screen width":self.screen_width}        

        # Create and set up the structure

        self.classes = {"button texts":ButtonText,
                        "eyes":Eye,
                        "closing eyes":ClosingEye,
                        "text fields":TextField,
                        "texts":DisplayedText,
                        "laceworks":Lacework,
                        "gears":Gear,
                        "strings":OscillatingString,
                        "clouds":Cloud,
                        "fingers":Finger,
                        "clocks":Clock,
                        "cheeses":Cheese,
                        "arrows":Arrow}
        
        self.elements ={"button texts":[],
                        "text fields":[],
                        "texts":[],
                        "eyes":[],
                        "closing eyes":[],
                        "laceworks":[],
                        "gears":[],
                        "strings":[],
                        "clouds":[],
                        "fingers":[],
                        "clocks":[],
                        "cheeses":[],
                        "arrows":[]}

        # Load the elements of the slide

        with open(f"Structure/{identifiant}.json") as f:
            data = json.load(f)['main']
            f.close()

        # Create the objects corresponding in the json file

        for category,element_list in data.items():
            for element in element_list:
                self.elements[category].append(self.classes[category](*element.values(),self.addons))

        if identifiant == "dictionary": self.create_spaced_texts()
        elif identifiant == "completion": self.create_gapped_texts()
           
    def create_spaced_texts(self):
        # Create the displayed examples of generated words
        temp_collapsed_text = wfca.CollapsedText()
        generated_words =  temp_collapsed_text.generate_spaced_text(200,"Texts/FrenchCorpus.txt","A","er!",2)
        generated_words = list(set(generated_words))
        generated_words.sort()
        
        # Create the associated elements
        rows = [5,6,5]
        for j in range(3):
            for i in range(rows[j]):
                x = 1/(1/3.15+(j/4.6))
                y = 1/(1/5.2+(i/15)-(j%2)/24)
                self.elements["button texts"].append(ButtonText(x,y,generated_words[i+j*5],[None,None],3,True,0,self.addons))
                    
    def create_gapped_texts(self):
        # Create the displayed examples of generated words
        temp_collapsed_text = wfca.CollapsedText()
        generated_words =  temp_collapsed_text.generate_gapped_text(50,"Texts/FrenchCorpus.txt","P____ine")
        generated_words = list(set(generated_words))
        generated_words.sort()
        
        
        # Create the associated elements
        rows = [3,4,3]
        word_index = 0
        for j in range(3):
            for i in range(rows[j]):
                word_index += 14
                x = 1/(1/4.5+(j/5))
                y = 1/(1/5+(i/10)-(j%2)/24+((j+1)%2)/80)
                
                if (word_index)>= len(generated_words):
                    self.elements["button texts"].append(ButtonText(x,y,generated_words[i+j*5],[None,None],3,True,0,self.addons))
                    continue
                
                self.elements["button texts"].append(ButtonText(x,y,generated_words[i+j*5],[None,None],3,True,0,self.addons))

    def draw(self,screen,tick):
        screen.fill(self.background_color)

        all_elements = [el for category in self.elements.values() for el in category]
        for obj in all_elements:
            obj.draw(screen,tick)

    def update(self,requests,submits):
        for button_text in self.elements["button texts"]:
            button_text.update(requests)
        
        for text_field in self.elements["text fields"]:
            text_field.update(submits,requests)

        for cloud in self.elements["clouds"]:
            cloud.update(requests)
        
        for clock in self.elements["clocks"]:
            clock.update(requests)
        
        for gear in self.elements["gears"]:
            gear.update(requests)
        
        for finger in self.elements["fingers"]:
            finger.update()
        
        for text in self.elements["texts"]:
            text.update()

#=- Alphabetically ordered decoration elements -=#

class Arrow():
    def __init__(self,x,y,radius,inversed,addons):
        # Arrow attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.radius = int(addons["screen width"]/radius)
        self.inversed = inversed
        
        # Global attributes
        self.main_color = addons["colors"]["main color"]
        self.background_color = addons["colors"]["background color"]
          
    def draw(self,screen,tick):
        x,y = self.position
        # Draw the arrow body -> four segments
        
        for i in range(4):
            # Get the circle Ys
            self.circle_positions = [int(y-self.radius/2),int(y+self.radius/2)] if (i+self.inversed)%2 else  [int(y+self.radius/2),int(y-self.radius/2)] 
            # And the rect between the blank and colored circles
            self.rect_positions = to_rect(x,y,self.radius*2,self.radius)

            # Draw the colored one
            pygame.gfxdraw.filled_circle(screen,x,self.circle_positions[0],self.radius,self.main_color)
            pygame.gfxdraw.aacircle(screen,x,self.circle_positions[0],self.radius,self.main_color)
            # Draw the rect in between
            pygame.gfxdraw.filled_polygon(screen,self.rect_positions,self.main_color)
            pygame.gfxdraw.aapolygon(screen,self.rect_positions,self.main_color)
            # Draw the blank one
            pygame.gfxdraw.filled_circle(screen,x,self.circle_positions[1],self.radius,self.background_color)
            pygame.gfxdraw.aacircle(screen,x,self.circle_positions[1],self.radius,self.background_color)
            
            # Move X to the next segment
            x += self.radius*2 

        # Draw the arrow tip -> moving triangle

        x -= self.radius
        
        # Set the angle of the tip
        theta = -math.pi/4 + math.cos(tick/20+self.inversed*math.pi)*math.pi/5 - (self.inversed)*math.pi/2
        
        # Get the coordinates of the triangle of the tip
        trigon_position = [ int_vec((x+self.radius*math.cos(theta),y+self.radius*(math.sin(theta)+0.3))),
                            int_vec((x+self.radius*math.cos(theta+1.57),y+self.radius*(math.sin(theta+1.57)+0.3))),
                            int_vec((x+self.radius*math.cos(theta+3.141),y+self.radius*(math.sin(theta+3.141)+0.3)))]
        
        # Eventually draw the tip
        pygame.gfxdraw.filled_polygon(screen,trigon_position,self.main_color)
        pygame.gfxdraw.aapolygon(screen,trigon_position,self.main_color)
            
class ButtonText():
    def __init__(self,x,y,text,action,changing_type,underlined,cooldown,addons):
        # Button text attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.base_text = text # Initially displayed text
        self.action = action # Which action is done when the button is pressed
        self.changing_type = changing_type # Hover aspect
        self.underlined = underlined # Determine if the text is underlined
        self.cooldown_delay = cooldown # Set the cooldown between two presses
        self.cooldown = 0
        
        # Global attributes
        self.font = addons["fonts"][0] if action[0] else addons["fonts"][1]
        self.main_color = addons["colors"]["main color"]
        
        # Modifiers
        self.current_color = addons["colors"]["main color"] # Drawn color
        self.current_text = text # Displayed text
        self.altered = False # == True if the button is hovered
        self.increment = 0 # Animation variabme
        self.render_text()
        
    def render_text(self):
        # Renders the text and associate it its ux elements
        self.base_text_rendered = self.font.render(self.base_text,True,self.main_color)
        self.base_rect = pygame.rect.Rect(*self.position,*self.font.size(self.base_text))
        
        # Reset the data
        self.current_text = self.base_text
        self.current_render = self.base_text_rendered
        self.current_rect = pygame.rect.Rect(*self.position,*self.font.size(self.current_text))
        self.current_underline = pygame.rect.Rect(self.current_rect.x,self.current_rect.y+self.current_rect.height-3,self.current_rect.width,2)

    def reset(self):
        # Reset the data
        self.cooldown = max(0,self.cooldown-1)
        self.current_color = self.main_color
        self.current_text = self.base_text
        self.current_render = self.base_text_rendered
        self.current_rect = pygame.rect.Rect(*self.position,*self.font.size(self.current_text))
        self.current_underline = pygame.rect.Rect(self.current_rect.x,self.current_rect.y+self.current_rect.height-3,self.current_rect.width,2)
    
    def update_rendered_text(self):
        return self.font.render(self.current_text,True,self.current_color)
        
    def update(self,requests):
        self.reset()

        # Get if the button is hovered
        
        self.altered = self.current_rect.collidepoint(*pygame.mouse.get_pos())
        
        if not self.altered: return # Not hovered -> quit
        
        # If the button is clickable (coolodwn == 0) and there is a click process its action

        if pygame.mouse.get_pressed()[0] and self.action[0] and not self.cooldown:
            requests[self.action[0]].append(self.action[1])
            self.cooldown = self.cooldown_delay
            
        # Animation elements

        self.increment += 1

        if self.changing_type == 1:
            self.current_color = (120,100,82)
            self.current_text = self.base_text
            self.current_render = pygame.transform.flip(self.update_rendered_text(),False,True)
        elif self.changing_type == 2:
            self.current_color = (120,100,82)
            self.current_text =  self.base_text[(self.increment//20)% (len(self.base_text)):]+  self.base_text[:((self.increment//20)% (len(self.base_text)))]
            self.current_render = self.update_rendered_text()
        elif self.changing_type == 3:
            self.current_color = (120,100,82)
            self.current_text = self.base_text
            self.current_render = self.update_rendered_text()
            
    def draw(self,screen,tick=0):
        # Draw the text
        screen.blit(self.current_render,self.position)

        if not self.underlined: return
        
        # Draw the line below if it is underlined
        pygame.draw.rect(screen,self.main_color,self.current_underline)

class Cheese():
    def __init__(self,x,y,start_angle,end_angle,radius,addons):
        # Cheese attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.angle = int_vec([math.pi/start_angle,math.pi/end_angle]) # Range of angle between hole and abs
        self.radius = int(addons["screen width"]/radius) # Max distance between the cheese pos and hole
        
        # Global attributes
        self.main_color = addons["colors"]["main color"]
        
        # Determine amount and sizes of the holes, generate them
        self.holes = []
        self.hole_radius = [radius/13,radius/20,radius/20,radius/20,radius/8.5]
        self.holes_count = 30
        self.generate_holes()

    def generate_holes(self):
        # Generate all the holes
        for i in range(self.holes_count):
            # Hole attributes
            drawn_angle = random.randint(self.angle[0]*100,self.angle[1]*100)/100 
            drawn_radius = random.randint(0,self.radius*100)/100
            drawn_size = self.radius/random.randint(8,25)
            # Create the hole
            self.holes.append([int_vec(add_vec(self.position,[math.cos(drawn_angle)*drawn_radius,math.sin(drawn_angle)*drawn_radius])),drawn_size,random.random()*6.28])

    def draw(self,screen,tick):
        # Loop for each hole
        for i in range(self.holes_count):
            # Draw the aa-hole
            pygame.gfxdraw.aacircle(screen,*self.holes[i][0],int(self.holes[i][1]),self.main_color)
            pygame.gfxdraw.filled_circle(screen,*self.holes[i][0],int(self.holes[i][1]),self.main_color)

class Clock():
    def __init__(self,x,y,radius,looking,addons):
        # Clock attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.radius = addons["screen width"]/radius
        self.initial_radius = addons["screen width"]/radius
        self.looking = looking
        self.altered = False
        
        # Global attributes
        self.main_color = addons["colors"]["main color"] 
        self.altered_color = addons["colors"]["desaltered color"] 
        self.background_color = addons["colors"]["background color"]
        self.font = pygame.font.Font("mirage.otf",int(self.radius/3))
        
        # Set up the arrows and the "i"s
        self.arrows = 3
        self.arrows_infos = []
        self.max_arrow_angle = int(628/self.arrows)
        self.generate_arrows()
        
        self.i_delay = 0
        self.rendered_i = self.font.render("i",True,self.main_color)
        
    def update(self,requests):
        # Only update the looking clock
        if self.looking:
            return
        
        self.altered = get_mouse_distance(self.position) < self.radius*0.75
        
        # If the user clicks on, send the request 

        if not self.altered: return 

        if not pygame.mouse.get_pressed()[0]: return 

        requests["change slide"].append("main")
        
    def generate_arrows(self):
        # Get a random angle for the first arrow
        arrow_angle = random.randint(20,int(628/self.arrows))/100
        
        for i in range(self.arrows):
            # Create an arrow and update the next one angle
            self.arrows_infos.append([arrow_angle,random.randint(50,110)/100,random.randint(50,90),math.pi/12])
            arrow_angle += math.pi*2/self.arrows * random.randint(90,110)/100
    
    def draw_arrowing_clock(self,screen,tick):
        self.i_delay += 0.01*(1+self.altered)

        # Draw the bigger circle of the clock
        pygame.gfxdraw.filled_circle(screen,*int_vec(self.position),int(self.radius*0.75), self.altered_color if not self.altered else self.main_color)
        pygame.gfxdraw.aacircle(screen,*int_vec(self.position),int(self.radius*0.75), self.altered_color if not self.altered else self.main_color)
        # Draw the mecanism center of the clock
        pygame.gfxdraw.filled_circle(screen,*int_vec(self.position),int(self.radius*0.05),self.main_color if not self.altered else self.altered_color)
        pygame.gfxdraw.aacircle(screen,*int_vec(self.position),int(self.radius*0.05),self.main_color if not self.altered else self.altered_color)
        
        for i in range(self.arrows):
            # Update and set the angle of the arrow
            arrow_delay = 10*self.i_delay
            arrow_dtheta = arrow_delay*self.arrows_infos[i][3]

            angle = self.arrows_infos[i][0]+arrow_dtheta
            
            # Get the arrow offset and get the position of the end of the arrow
            arrow_lift = [self.radius*self.arrows_infos[i][1]*math.cos(angle),self.radius*self.arrows_infos[i][1]*math.sin(angle)]
            end_line = add_vec(self.position,arrow_lift)
            
            # Draw the end of the arrow
            pygame.gfxdraw.filled_circle(screen,*int_vec(end_line),int(self.radius*self.arrows_infos[i][1]*0.2), self.main_color if not self.altered else self.altered_color)
            pygame.gfxdraw.aacircle(screen,*int_vec(end_line),int(self.radius*self.arrows_infos[i][1]*0.2), self.main_color if not self.altered else self.altered_color)
            
            # Draw the arrow itself
            pygame.draw.line(screen,self.main_color if not self.altered else self.altered_color,self.position,end_line,3)

        # All the "i" orbiting around the clock
        for i in range(0,12):
            # Get offset and raw position
            spatched_i = [self.radius*1.5*math.cos(self.i_delay+2*math.pi*i/12),self.radius*1.5*math.sin(self.i_delay+2*math.pi*i/12)]
            spatched_i = add_vec(spatched_i,[-self.font.size("i")[0]/2,-self.font.size("i")[1]/2])
            screen.blit(self.rendered_i,add_vec(self.position,spatched_i))

    def draw_looking_clock(self,screen,tick):
        # Get some values
        mouse_angle = get_mouse_angle(self.position)
        circle_offset = [self.radius*0.35*math.cos(mouse_angle),self.radius*0.35*math.sin(mouse_angle)]
        eye_ball_position = add_vec(self.position,circle_offset)

        inner_circle_offset = [self.radius*0.35*math.cos(math.pi+mouse_angle),self.radius*0.35*math.sin(math.pi+mouse_angle)]

        segment_first_end = [self.radius*0.35*math.cos(mouse_angle),self.radius*0.35*math.sin(mouse_angle)]
        segment_second_end = [self.radius*math.cos(math.pi+mouse_angle),self.radius*math.sin(math.pi+mouse_angle)]

        # Opposite direction inner circle
        pygame.gfxdraw.aacircle(screen,*int_vec(add_vec(self.position,inner_circle_offset)),int(self.radius*0.5), self.altered_color)
        pygame.gfxdraw.filled_circle(screen,*int_vec(add_vec(self.position,inner_circle_offset)),int(self.radius*0.5), self.altered_color)
        pygame.gfxdraw.aacircle(screen,*int_vec(add_vec(self.position,inner_circle_offset)),int(self.radius*0.25), self.background_color)
        pygame.gfxdraw.filled_circle(screen,*int_vec(add_vec(self.position,inner_circle_offset)),int(self.radius*0.25), self.background_color)

        # Right direction inner circle
        pygame.gfxdraw.aacircle(screen,*int_vec(eye_ball_position),int(self.radius*0.3), self.main_color)
        pygame.gfxdraw.filled_circle(screen,*int_vec(eye_ball_position),int(self.radius*0.3), self.main_color)
        pygame.gfxdraw.aacircle(screen,*int_vec(eye_ball_position),int(self.radius*0.1), self.background_color)
        pygame.gfxdraw.filled_circle(screen,*int_vec(eye_ball_position),int(self.radius*0.1), self.background_color)

        # Line between the two
        
        pygame.draw.line(screen,self.background_color,add_vec(self.position,segment_first_end),add_vec(self.position,segment_second_end),5)

        # Blank outer circle and colored outer circle
        pygame.draw.circle(screen,self.background_color,self.position,int(self.radius),int(self.radius*0.45))

        pygame.draw.circle(screen,self.altered_color,self.position,self.radius*1.01,int(self.radius*0.2))
        pygame.gfxdraw.aacircle(screen,*int_vec(self.position),int(self.radius*1.01), self.altered_color)
        pygame.gfxdraw.aacircle(screen,*int_vec(self.position),int(self.radius), self.background_color)
    
    def draw(self,screen,tick):
        return self.draw_looking_clock(screen,tick) if self.looking else self.draw_arrowing_clock(screen,tick)

class ClosingEye():
    def __init__(self,x,y,radius,addons):
        # Closing Eye attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.radius = int(addons["screen width"]/radius)
        
        # Global attributes
        self.main_color = addons["colors"]["main color"]
        self.background_color = addons["colors"]["background color"] 

    def draw(self,screen,tick):
        decreasing = int(self.radius*(0.5+0.5*abs(math.cos(tick/80))))
        
        # First inner circle
        pygame.gfxdraw.aacircle(screen,*self.position,self.radius, self.main_color)
        pygame.gfxdraw.filled_circle(screen,*self.position,self.radius, self.main_color)
        
        # Breathing circle
        pygame.gfxdraw.aacircle(screen,self.position[0],self.position[1]-self.radius,decreasing, self.background_color)
        pygame.gfxdraw.filled_circle(screen,self.position[0],self.position[1]-self.radius,decreasing, self.background_color)

        # Draw the irises

        mouse_angle = get_mouse_angle(self.position)

        # First iris, moving in direction to the mouse

        iris_position = int_vec((self.position[0]+0.5*self.radius*math.cos(mouse_angle),self.position[1]+0.5*self.radius*math.sin(mouse_angle)))

        pygame.gfxdraw.aacircle(screen,*iris_position,int(self.radius/3), self.background_color)
        pygame.gfxdraw.filled_circle(screen,*iris_position,int(self.radius/3), self.background_color)

        # Second iris

        iris_position = int_vec((self.position[0]+0.6*self.radius*math.cos(mouse_angle),self.position[1]+0.6*self.radius*math.sin(mouse_angle)))
        
        pygame.gfxdraw.aacircle(screen,*iris_position,int(self.radius/5), self.main_color)
        pygame.gfxdraw.filled_circle(screen,*iris_position,int(self.radius/5), self.main_color)

class Cloud():
    def __init__(self,x,y,radius,addons):
        # Cloud attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.radius = addons["screen width"]/radius 
        self.altered = False
        
        # Global attributes
        self.main_color = addons["colors"]["main color"] 
        self.background_color = addons["colors"]["background color"] 
        self.altered_color = addons["colors"]["altered color"]
        
        # Create the waterflows
        x = self.position[0]
        y = self.position[1]
        self.water_flows = [WaterFlow(x,y-self.radius,self.main_color,self.radius*2),WaterFlow(x+self.radius*1.1,y-self.radius*1.5,self.main_color,self.radius*3),WaterFlow(x-self.radius*1.3,y+self.radius*0.2,self.main_color,self.radius*3)]
        
        # Set up the text in the center
        self.font = pygame.font.Font("mirage.otf",int(self.radius))
        self.text = "III"
        self.base_render = self.font.render(self.text,True,self.background_color)
        self.altered_render = self.font.render(self.text,True,self.altered_color)
        self.current_render = self.base_render 

        # Set centered text properties
        self.letter_dxy = [s/2 for s in self.font.size(self.text)]
        self.letter_rect = self.base_render.get_rect()
        self.letter_rect.x,self.letter_rect.y = self.position[0]-self.letter_dxy[0],self.position[1]-self.letter_dxy[1]

    def update(self,requests):
        self.current_render = self.base_render
        self.altered = self.letter_rect.collidepoint(*pygame.mouse.get_pos())

        if not self.altered: return 

        self.current_render = self.altered_render

        if not pygame.mouse.get_pressed()[0]: return 

        requests["change slide"].append("main")

    def draw(self,screen,tick):
        #-- Draw the cloud itself --#

        # The main circle of the cloud
        pygame.gfxdraw.aacircle(screen,*self.position,int(self.radius), self.main_color)
        pygame.gfxdraw.filled_circle(screen,*self.position,int(self.radius), self.main_color)

        # The auxilaries circles #

        iterated_circles = [[-self.radius,self.radius/10,int(self.radius/1.3)],
                            [-self.radius/1.5,-self.radius/2,int(self.radius/2.5)],
                            [self.radius/1.1,self.radius/9,int(self.radius/1.4)],
                            [self.radius/1.5,self.radius/2,int(self.radius/2.5)],]

        for i in range(len(iterated_circles)):
            iterated_circle_position = int_vec([self.position[0]+iterated_circles[i][0],
                                        self.position[1]+iterated_circles[i][1],])

            pygame.gfxdraw.aacircle(screen,*iterated_circle_position,iterated_circles[i][2], self.main_color)
            pygame.gfxdraw.filled_circle(screen,*iterated_circle_position,iterated_circles[i][2], self.main_color)


        # The water drops #

        for water_flow in self.water_flows:
            water_flow.draw(screen,tick)

        screen.blit(self.current_render,[self.position[0]-self.letter_dxy[0],self.position[1]-self.letter_dxy[1]])

class DisplayedText():
    def __init__(self,x,y,text,addons):
        # Displayed text attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.base_text = text
        
        # Global attributes
        self.font = addons["fonts"][2]
        self.main_color = addons["colors"]["main color"]
        self.screen_width = addons["screen width"]
        
        # Animation settings
        self.animation_delay = 15 # time in tick between two changements
        self.animation_counter = 0 # timer 
        self.animation_index = 0 # index of the letter capitalized (Workers of the world unite; you have nothing to lose but your chains.)
        self.animated_texts = []
        self.render_text()
        self.render_animated_texts()

    def render_animated_texts(self):
        for i in range(len(self.base_text)):
            # Get the text as a list
            text = list(self.base_text.lower())
            # Capitalize one
            text[i] = text[i].upper()
            # Turn back into text
            self.base_text = "".join(text)
            # Render and store 
            self.render_text()
            self.animated_texts.append(self.rendered_text)

    def render_text(self):
        self.rendered_text = self.font.render(self.base_text,True,self.main_color)
        
    def update(self):
        # Update the counter
        self.animation_counter = max(0,self.animation_counter-1)
        
        if self.animation_counter: return 
        
        self.animation_index += 1 #update index
        self.animation_counter = self.animation_delay #update counter
        self.rendered_text = self.animated_texts[self.animation_index%(len(self.base_text))] # set the new rendered
            
    def draw(self,screen,tick):
        screen.blit(self.rendered_text,self.position)

class Eye():
    def __init__(self,x,y,radius,harmonics,addons):
        # Eye attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.radius = addons["screen width"]/radius
        self.harmonics = harmonics
        self.precision = 20
        
        # Global attributes
        self.main_color = addons["colors"]["main color"] 
        self.background_color =  addons["colors"]["background color"] 
        
        # Render and specify letters drawn inside the eyeballs
        self.delay = random.randint(0,10)
        self.letters = "dictionary                        "
        self.rendered_letters = {}
        self.initialize_letters(addons["fonts"][1])

    def initialize_letters(self,font):
        # Get all the unique letters in my text
        unique_letters = "".join(set(self.letters))
        for i in range(len(unique_letters)):
            # Render each letter
            self.rendered_letters[unique_letters[i]] = [font.render(unique_letters[i],True,self.background_color),font.size(unique_letters[i])]
  
    def draw(self,screen,tick):
        # Get the mouse position to make the iris follow the cursor
        mouse_angle = get_mouse_angle(self.position)

        # Get the stretched iris position
        iris_position = int_vec(generate_elipsoid(self.position,mouse_angle,self.radius/3,self.harmonics,tick))

        # Draw the iris
        pygame.gfxdraw.aacircle(screen,*iris_position,int(self.radius/2.5), self.main_color)
        pygame.gfxdraw.filled_circle(screen,*iris_position,int(self.radius/2.5), self.main_color)


        # Get wich letter has to be drawn inside the iris
        letter = self.letters[(self.delay + tick // 50) % len(self.letters)]

        # Draw the letter

        iris_position[0] -= self.rendered_letters[letter][1][0]/2
        iris_position[1] -= self.rendered_letters[letter][1][1]/2
        screen.blit(self.rendered_letters[letter][0],iris_position)

        # Draw the outline of the eyeball

        for i in range(int(6.31*self.precision)):
            outline_position = int_vec(generate_elipsoid(self.position,i/self.precision,self.radius,self.harmonics,tick))
            pygame.gfxdraw.filled_circle(screen,*outline_position,1, self.main_color)
  
class Finger():
    def __init__(self,x,y,length,angle,inverted,addons):
        # Finger attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.base_length = addons["screen width"]/length
        self.ultimate_base_length = addons["screen width"]/length
        self.base_angle = math.pi/angle
        self.ultimate_base_angle = math.pi/angle
        self.cooldown = 0 # Cooldown between two phalanx-cut
        self.phalanx_count = 4 # Number of phalanx
        self.inverted = (-1)**inverted 


        # Global attributes
        self.main_color = addons["colors"]["desaltered color"] 
        self.background_color = addons["colors"]["background color"]  
        self.altered_color = addons["colors"]["main color"] 
        self.used_colors = [self.altered_color,self.main_color]
        
        # Determination of more specifics finger's caracteristics

        self.angle_speed = random.randint(120,150)
        self.angle_delay = random.randint(0,62)/10

        self.length_speed = random.randint(90,110) # How fast the phalanx stretches
        self.length_delay = random.randint(0,62)/10

        self.angle_amplitude = random.randint(10,20)/100
        self.length_amplitude = random.randint(10,20)/100 # How much the phalanx stretches

        self.dtheta_delay = random.randint(0,62)/10
        self.dtheta_amplitude= random.randint(8,20)/100
        self.dtheta = 0

    def update(self):
        # Phalanx cutting
        
        self.cooldown = max(0,self.cooldown-1)
        
        if get_mouse_distance(self.position)>100 or not pygame.mouse.get_pressed()[0]:
            return
        if self.cooldown > 0 or self.phalanx_count<3:
            return 
        
        # If the phalanx is cutable, cut it and modify its properties

        self.cooldown = 20
        self.phalanx_count -= 1
        self.dtheta_amplitude *= 3
        
    def draw(self,screen,tick):
        # Angle, length and angle offset used for all the finger, that depends of time
        self.base_angle = self.ultimate_base_angle * (1+self.angle_amplitude*math.cos(self.angle_delay+tick/self.angle_speed))
        self.base_length = self.ultimate_base_length* (1+self.length_amplitude*math.cos(self.length_delay+tick/self.length_speed))/1.3
        self.dtheta = self.dtheta_amplitude*math.cos(self.dtheta_delay+tick/10)
        # Get the width of the finger in function the length of a single segment
        self.width = self.base_length  / 5

        # Draw the finger and its shadow
        for j in range(2):
            last_joint_pos = add_vec(self.position,[5,5]) if not self.inverted + 1 else add_vec(self.position,[5,-5])
            
            # Draw the very beginning of the finger
            pygame.draw.circle(screen,self.used_colors[j],last_joint_pos,self.width/2)
            
            for i in range(self.phalanx_count):
                # Phalanx properties
                curbature = self.inverted*math.pi/(self.phalanx_count-i) if i else i 
                current_angle = self.base_angle-curbature-self.inverted*self.dtheta*i
                current_length = self.base_length/(i+1) if i else 0.7*self.base_length

                # Position of the end of the phalanx
                joint = add_vec(last_joint_pos,[current_length*math.cos(-current_angle),current_length*math.sin(-current_angle)])

                phax_joint = [[0.5*self.width*math.cos(-current_angle-math.pi/2),0.5*self.width*math.sin(-current_angle-math.pi/2)],[0.5*self.width*math.cos(-current_angle+math.pi/2),0.5*self.width*math.sin(-current_angle+math.pi/2)]]
            
                phalanx = [add_vec(last_joint_pos,phax_joint[0]),add_vec(last_joint_pos,phax_joint[1]),add_vec(joint,phax_joint[1]),add_vec(joint,phax_joint[0])]
            
                # Draw the rectangular part of the phalanx
                pygame.draw.polygon(screen,self.used_colors[j],phalanx)
                pygame.draw.aaline(screen,self.used_colors[j],int_vec(phalanx[0]),int_vec(phalanx[1]),3)
                pygame.draw.aaline(screen,self.used_colors[j],int_vec(phalanx[1]),int_vec(phalanx[2]),3)
                pygame.draw.aaline(screen,self.used_colors[j],int_vec(phalanx[2]),int_vec(phalanx[3]),3)
                pygame.draw.aaline(screen,self.used_colors[j],int_vec(phalanx[3]),int_vec(phalanx[0]),3)
                
                # Draw the end of the phalanx : nail / junction
                pygame.gfxdraw.aacircle(screen,*int_vec(joint),int(1.06*self.width/2), self.used_colors[j])
                pygame.gfxdraw.filled_circle(screen,*int_vec(joint),int(1.06*self.width/2), self.used_colors[j])

                last_joint_pos = joint
            
            
            last_joint_pos = self.position
            self.base_length *= 1.3
            self.width = self.base_length  / 5

class Gear():
    def __init__(self,x,y,radius,text,addons):
        # Gear attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.radius = addons["screen width"]/radius
        self.text = text
        self.tick = 0
        self.altered = False
        
        # Global attributes
        self.main_color = addons["colors"]["main color"]
        self.background_color = addons["colors"]["main color"]
        self.screen_width = addons["screen width"]
        self.font = pygame.font.Font("mirage.otf",int(self.screen_width/24))
        self.font_small = pygame.font.Font("mirage.otf",int(self.screen_width/60))
        
        self.text_rendered = [self.font.render(self.text,True,self.main_color),self.font_small.render("a",True,self.main_color),self.font_small.render("r"if text=="P" else "ck",True,self.main_color)]
        

    def update(self,requests):
        self.altered = get_mouse_distance(self.position)<50
        
        if not pygame.mouse.get_pressed()[0] or not self.altered: return 
        
        # Send request if the user clicks on the center
        
        requests["change slide"].append("parameters" if self.text == "P" else "dictionary")

    def draw(self,screen,tick=0):
        self.tick += 1*(1-2*self.altered)*(1+self.altered)
        
        # Draw the center
        screen.blit(self.text_rendered[0],self.position)

        # Draw the orbital letters arround 
        dx = self.screen_width/240
        orbital_pos = dx+self.position[0]+math.cos(self.tick/(dx*8))*dx*6,3*dx+self.position[1]+math.sin(self.tick/(dx*8))*dx*6
        screen.blit(self.text_rendered[1],orbital_pos)
        orbital_pos = dx+self.position[0]+math.cos(2*dx+self.tick/(dx*6))*dx*6,3*dx+self.position[1]+math.sin(2*dx+self.tick/(dx*6))*dx*10
        screen.blit(self.text_rendered[2],orbital_pos)

class Lacework():
    def __init__(self,x,y,radius,harmonics,linked,addons):
        # Lacework attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.initial_radius = addons["screen width"]/radius
        self.harmonics = harmonics
        self.linked = linked
        
        # Global attributes
        self.main_color = addons["colors"]["main color"]
        
        # Number of points per layer
        self.precision = 5 if linked else 15
        # Nummber of layers
        self.iterations = 8
        
    def draw(self,screen,tick):
        # For each layer
        for j in range(self.iterations):
            # Get the layer distance
            radius = self.initial_radius - self.initial_radius/18 * j
            
            if self.linked:
                # Draw a line between the two points
                pygame.draw.aalines(screen,self.main_color,True,[int_vec(generate_elipsoid(self.position,i/self.precision,radius,self.harmonics,tick)) for i in range(int(6.31*self.precision))],1)
                continue 
            
            for i in range(int(6.31*self.precision)):
                # Draw the points                
                pygame.gfxdraw.filled_circle(screen,*int_vec(generate_elipsoid(self.position,i/self.precision,radius,self.harmonics,tick)),1,self.main_color)

class OscillatingString(): 
    def __init__(self,x,y,length,addons):
        # Oscillating String attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.length = addons["screen width"]/length
        self.precision = 80 # Number of vertical layers
        
        # Global attributes
        self.screen_width = addons["screen width"]
        self.main_color = addons["colors"]["main color"]
        
        # Harmonics of the cos / sin waves
        self.harmonics = [[2,0.3,40,random.randint(0,5)/5],[1,0.05,50,0.5],[4,0.1+random.randint(1,5)/100,500,0.5]]

    def draw(self,screen,tick):
        factor = self.screen_width/24
        line_width = max(1,int(self.screen_width/600))

        # Get and draw the first excentricity
        first_exc = factor*generate_excentricity(0,self.harmonics,tick)
        pygame.draw.line(screen,self.main_color,(self.position[0]-first_exc,self.position[1]),(self.position[0]+first_exc,self.position[1]),2)
        # Get and draw the second excentricity
        first_exc = factor*generate_excentricity((self.precision-1)/(factor/5),self.harmonics,tick)
        pygame.draw.line(screen,self.main_color,(self.position[0]-first_exc,self.position[1]+(self.precision-1)*self.length/self.precision),(self.position[0]+first_exc,self.position[1]+(self.precision-1)*self.length/self.precision),line_width)
        pygame.draw.line(screen,self.main_color,(self.position[0],self.position[1]+(self.precision-1)*self.length/self.precision),(self.position[0],2000),line_width)
        
        # For each layer draw the line
        for i in range(self.precision):
            # Get excentricity
            exc = generate_excentricity(i/(factor/5),self.harmonics,tick)
            
            # Get offsets
            dx = factor*exc
            dy = i*self.length/self.precision
            pygame.draw.line(screen,self.main_color,(self.position[0]-dx,self.position[1]+dy),(self.position[0]-dx-exc*(factor/2.5),self.position[1]+dy),line_width)
            pygame.draw.line(screen,self.main_color,(self.position[0]+dx,self.position[1]+dy),(self.position[0]+dx+exc*(factor/2.5),self.position[1]+dy),line_width)

class TextField():
    def __init__(self,x,y,text,decoration,searching,addons):
        #  Text field attributes
        self.position = int_vec((addons["screen width"]/x,addons["screen width"]/y))
        self.base_text = text
        self.decoration = decoration # What to put when there is no text, or before / after
        self.searching = searching # Action when writting
        
        # Global attributes
        self.main_color = addons["colors"]["main color"] 
        self.font = addons["fonts"][0] 
        self.altered_color =(120,100,82)
        
        # Setting up text
        self.current_text = self.base_text
        self.current_render = self.font.render(decoration[0]+self.current_text+decoration[1],True,self.main_color)
    
    def draw(self,screen,tick=0):
        screen.blit(self.current_render,self.position)

    def update(self,submits,requests):
        if not submits["key_pressed"]: return 
        
        # Process the letter pressed
        key_pressed =  submits["key_pressed"][0]
        self.current_text = process_letter(self.current_text,key_pressed,self.searching)
        
        if self.current_text:
            self.current_text = self.current_text[0].upper() + self.current_text[1:]
        
        # Send up the request
        requests["change "+self.searching].append(self.current_text)
        
        # Change the current text rendered in function of what has been written
        if self.current_text !="":
            self.current_render = self.font.render(self.decoration[0]+self.current_text+self.decoration[1],True,self.main_color)
        else:
            self.current_render = self.font.render(self.decoration[2],True,self.altered_color)

class WaterFlow():
    def __init__(self,x,y,main_color,length):
        # Waterflow attributes
        self.start_pos = x,y
        self.length = length
        self.waves = 2
        self.speed = 1
        
        self.steps = 100
        self.current_step = 0
        self.delay = random.randint(0,self.steps)
        
        # Global attributes
        self.main_color = main_color
        self.render = pygame.font.Font("mirage.otf",int(length/5)).render("i",True,self.main_color)

    def draw(self,screen,tick): 
        self.current_step = (self.delay+ tick//self.speed)%self.steps
        # Draw the ascending I
        screen.blit(self.render,[self.start_pos[0],self.start_pos[1]-self.length*self.current_step/self.steps])


