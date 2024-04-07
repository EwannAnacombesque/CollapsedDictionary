import random

class CollapsedText():
	def __init__(self,verbose=False):
		self.file_name =  ""
		self.content = ""
		self.content_size = 0
		self.characters_list = []
		self.characters_dict = {}
		self.divertsity_count = 0

		self.ambidextrous_probability_table = []
		self.depth_argument = 0
		self.verbose = verbose
		self.ponctuations_marks = [".","!","?"]
		self.random_letters = "abcdefghijlkmnopqrstuvwxyzêûç"
		self.vowels = "aeiouyéè"
		self.last_ponctuation_mark = 0


		self.unknown_char = "_"
		self.double_vision = False 

		#Word lengh managing 

		self.length_list = []
		self.resumed_content = []
		self.length_probability_table = []

		#  word_ends 

		self.word_ends_probability_table = []

		if self.verbose: self.introduce_program()		

	def introduce_program(self):
		print("--==--==--==--==---==--==--==--==--")
		print("==-       -{WFCAnalogue}-       -==")
		
	def initialize(self):
		self.create_conjugation()
		self.read_file()
		
		self.update_characters_dict()
		self.ambidextrous_probability_table = self.create_ambidextrous_probability_table(self.divertsity_count,self.depth_argument)
		self.set_probabilities(self.content,self.ambidextrous_probability_table,self.depth_argument,True)
		
		self.lengthify()

		self.create_word_word_ends()

#==- Reading and analyzing file -==#

	def read_file(self):
		with open(self.file_name,"rt",encoding="utf-8") as f:
			self.content = f.read()
		
		self.content = self.content.replace("\n"," ")
		

		self.initial_word_length = self.extract_data(self.content)

		self.content_size = len(self.content)

		self.characters_list = []

		for character in self.content:
			if character.lower() not in self.characters_list:
				self.characters_list.append(character.lower())

		self.divertsity_count = len(self.characters_list)
		
		if self.verbose:  
			print("===================================")
			print("---=== Reading File ===---")
			print("File name : "+self.file_name)
			print("File length : "+str(len(self.content)))
			print("Unique characters : "+str(self.divertsity_count))

	def update_characters_dict(self):
		self.characters_dict = {}
		for i,character in enumerate(self.characters_list):
			self.characters_dict[character] = i

#==- Annex -==#

	def lengthify(self):
		self.resumed_content = [len(word.replace(" ","")) for word in self.content.split(" ") if word]

		local_depth_argument = 1
		self.length_probability_table = self.create_ambidextrous_probability_table(max(self.resumed_content)+1,local_depth_argument)
		self.set_probabilities(self.resumed_content,self.length_probability_table,local_depth_argument,False)

	def create_word_word_ends(self):
		# Create the probability table

		# following blueprint : table[length][start or end][char]

		for lengths in range(max(self.resumed_content)+1):
			self.word_ends_probability_table.append([])
			for position in range(2):
				self.word_ends_probability_table[lengths].append([])
				for char in range(len(self.ambidextrous_probability_table)):
					self.word_ends_probability_table[lengths][position].append(0)
		
		# fill this table 

		self.set_word_ends_probabilities(self.word_ends_probability_table)

#==- Compute probabilities -==#

	def create_ambidextrous_probability_table(self,element_count,depth_argument):
		# ambidextrous_probability_table[subject letter][forward][layer][object letter]

		table = []
		for subject_letter in range(element_count):
			# Create each subject letter its probability table 
			table.append([])

			for direction in range(2):
				# Create each direction for each subject letter
				table[subject_letter].append([])

				# Create each layer for each subject direction 
				for layer in range(depth_argument):
					table[subject_letter][direction].append([])

					# Create each object letter for each layer
					for object_letter in range(element_count):
						table[subject_letter][direction][layer].append(0)
		
		return table
	
	def set_word_ends_probabilities(self,table):

		word_ends = [[len(word),word[0].lower(),word[-1].lower()] for word in self.content.replace("\n","").split(" ") if word]

		for word in word_ends:
			if word =="":
				continue
			for position in range(2):
				table[word[0]][position][self.get_id(word[1+position],True)] += 1

	def set_probabilities(self,content,table,depth_argument,letter):
		for i in range(len(content)):
			guess_id = self.get_id(content[i],letter)

			#additionnal forbidden char "’"
			strength = 1
			if letter:
				strength = self.space_factors[0] if (content[i] not in [" ",",","à","û"]) else self.space_factors[1]

			# Get the values for each layer of depth

			self.get_layers_values(content,table,i,guess_id,strength,depth_argument,letter)

	def get_layers_values(self,content,table,character_index,character_id,strength,depth_argument,letter):
		# Enumerating each layer k

		depth_factors = self.depth_factors if letter else [4,1,1,1,1,1]

		content_size = len(content)
		
		# Look forward

		for layer in range(depth_argument):
			# Making sure that it doesn't look at a letter that doesn't exist yet

			if (character_index<=layer) : continue

			target_id = self.get_id(content[character_index-(layer+1)],letter)

			# Adding the value to the probability table 
			
			table[target_id][0][layer][character_id] += depth_factors[layer]*strength
		
		# Look backward

		for layer in range(depth_argument):
			# Making sure it doesn't look at a letter that overlap
			
			if (content_size-character_index<=layer+1): continue

			target_id = self.get_id(content[character_index+(layer+1)],letter)

			table[target_id][1][layer][character_id] += depth_factors[layer]*strength

	def mix_layers(self,probability_layers,layers_summations,depth,mix_factors=[1,3,4,5,1,1,1,1]):
		stage_layer = []
		for i in range(len(probability_layers[0])):
			temp_prob = 0
			for d in range(depth):
				if (not layers_summations[d]): continue


				temp_aditionnal_value = 1

				for n in range(d+1):
					temp_aditionnal_value *= probability_layers[n][i]



				temp_prob += temp_aditionnal_value * mix_factors[d]
			stage_layer.append(temp_prob)

		return stage_layer

	def mix_directions(self,ambidextrous_probability_layers,smooth_mix=True):
		unified_stage_layers = []

		
		for layer in range(len(ambidextrous_probability_layers)):
			temp_layer = []

			for object_letter in range(len(ambidextrous_probability_layers[0][0])):
				temp_prob = ambidextrous_probability_layers[layer][0][object_letter]*ambidextrous_probability_layers[layer][1][object_letter]

				if smooth_mix:
					temp_prob *= 2
					temp_prob += ambidextrous_probability_layers[layer][0][object_letter] + ambidextrous_probability_layers[layer][1][object_letter] 
				
				
				temp_layer.append(temp_prob)
			


			unified_stage_layers.append(temp_layer)
		return unified_stage_layers

	def draw_character(self,probability_layers,depth_argument):
		# Get each layer summation

		layers_summations = [sum(layer) for layer in probability_layers]

		# If the main layer says it's impossible, so give up

		if (not layers_summations[0]) :
			print("First layer summation is null - Critical issue")
			return '!'

		#- Get the final raw probabilities -#

		raw_probabilities = self.mix_layers(probability_layers,layers_summations,depth_argument)
		raw_summation = sum(raw_probabilities)

		if (not raw_summation) : return "!"

		# Get the probabilities intervals with the raw probabilities

		probabilities_intervals = self.create_probabilities_intervals(raw_probabilities)

		# Draw the character 

		draw_index = self.draw_element(raw_summation,probabilities_intervals)

		return draw_index

	def create_probabilities_intervals(self,raw_probabilities):
		probabilities_intervals = []
		last_interval_min = 0

		# Transform a sequence of raw probabilities in a indexed list of intervals

		for i,prob in enumerate(raw_probabilities):
			# If the prob is 0 then pass

			if (not prob): continue 

			# Else add and store the index

			last_interval_min += prob 

			probabilities_intervals.append([last_interval_min,i])

		# Turn [0,2,0,3] into [(2,1),(5,3)] for example
		

		return probabilities_intervals

	def draw_element(self,max_value,probabilities):
		# Draw a number in the good range 

		drawn_number = random.randint(0,max_value-1)

		# Is gonna be the index, set as 0 for now

		drawn_index = 0
		
		last_step = 0
		for step in probabilities:
			# Verify if the drawn number is in the right interval / step 

			if drawn_number >= last_step and drawn_number < step[0]:
				drawn_index = step[1]
				break
			
			# Else update the interval

			last_step = step[0]

		return drawn_index

#==- Utility functions -==#

	def get_id(self,subject,letter):
		if letter: return self.characters_dict[subject.lower()]

		return subject

	def get_char(self,index):
		return self.characters_list[index]

	def capitalize(self,text,index):
		text = list(text)
		text[index] = text[index].upper()
		return "".join(text)
	
	def is_end_of_word(self,text,ends):
		for end in ends:
			if text[-len(end):].lower() == end.lower():
				return True 

	def add_punctuation(self,text):
		self.last_ponctuation_mark += 1

		if len(text) > 4: # Make sure the text is enough long 
			if text[-3] in self.ponctuations_marks:
				text = self.capitalize(text,-1)
		
		if 	self.last_ponctuation_mark > random.randint(10,40) and text[-1] == " " and random.randint(0,10) < 2:
			text = text[:-1] + "."
			self.last_ponctuation_mark = 0 
				
		return text

#==- Generate text and/or words -==#

	#- Generate parts of text -#

	def generate_ambidextrous_character(self,text,subject_index):
		# Make sure to get the layers it needs

		sent_layers = self.get_sent_ambidextrous_layers(self.ambidextrous_probability_table,text,subject_index,self.depth_argument,True)

		unified_sent_layers = self.mix_directions(sent_layers,True)

		# Generate an index with those layers

		generated_index = self.draw_character(unified_sent_layers,self.depth_argument)

		if generated_index == "!": 
			if self.verbose:
				print("couldn't generate anything - Critical issue")
				print(text)
				print(self.get_sent_probability_table(text,0,subject_index,len(text),False)[1])
				print("Index : "+str(subject_index))

			#return os.abort()
			text = " Failed."
			return text

		# Translate it into char and add it to the text

		text = text[:subject_index] + self.get_char(generated_index) + text[subject_index+1:]


		return text

	def generate_string(self,text,string_length,stop_at,max_string_length):
		# Create a string and expand it 

		for i in range(string_length):
			# Add the collapsed character 

			text = self.generate_character(text)

			# Add the punctuation
			text = self.add_punctuation(text)
			
			# If the conditions are verified, stop the string now
			if self.stop_generate_string(text,stop_at,i,max_string_length) : break

		
		return text

	def generate_gapped_text(self,enumerations,file_name,seed):
		self.initialize_generation(file_name,3,[1,0],[6,3,2,1,1,1,1,1])

		if self.verbose:
			print("===================================")
			print("---=== Word Generation ===---")
			print("[Generating letters in place of gap in the word]")
			print("-> The seed is : "+seed.replace("_","-").replace("!"," "))
	
		seed = seed.replace("!"," ")
		seed = " "+seed
		
		if seed == " ":
			return []

		# Good settings 4 ; [5,3,2,1,1,1,1,1] ; [1,3,4,5,1,1,1,1]

		saved_strings = []

		repeated_times = 1
		
		if self.unknown_char not in seed:
			return self.conclude_generation([self.capitalize(seed[1:],0)],enumerations*repeated_times)
		

		for count in range(enumerations):

			gap_count = seed.count(self.unknown_char)
			last_gap_index = seed.index(self.unknown_char)
			word = seed

			for i in range(gap_count):

				word = self.generate_ambidextrous_character(word,last_gap_index)
				last_gap_index = self.get_first_gap(word)
				
				if word == " Failed.":
					break				

			word = word[1:]
			word = self.capitalize(word,0)
			saved_strings.append(word)
		

		saved_strings = self.conclude_generation(saved_strings,enumerations*repeated_times)
		return saved_strings
	
	def generate_spaced_text(self,enumerations,file_name,start_seed,end_seed,filling,strict=True):
		self.initialize_generation(file_name,3,[1,0],[6,3,2,1,1,1,1,1])

		if self.verbose:
			print("===================================")
			print("---=== Word Generation ===---")
			print("[Generating letters in between ends of the word]")
			print(f"-> The seed is : {start_seed} [...] {end_seed}")
	
		start_seed = start_seed.replace("!"," ")
		end_seed = end_seed.replace("!"," ")
		start_seed = " "+start_seed

		end_seed = end_seed

		word_boundaries = [filling,filling+2*strict]
		saved_strings = []


		for count in range(enumerations):
			increasing_length = random.randint(*word_boundaries)
			word = start_seed + "_"*increasing_length+ end_seed


			for i in range(increasing_length):
				word = self.generate_ambidextrous_character(word,i+len(start_seed))

				if word == " Failed.":
					break				


			word = word[1:]
			word = self.capitalize(word,0)
			saved_strings.append(word)
		

		saved_strings = self.conclude_generation(saved_strings,enumerations)
		return saved_strings

	#- Generate whole sentences -#

	def generate_word_length(self,former_words,local_depth_argument):
		sent_layers = self.get_sent_ambidextrous_layers(self.length_probability_table,former_words+["_"],len(former_words),local_depth_argument,False)

		unified_sent_layers = self.mix_directions(sent_layers,True)

		generated_length = self.draw_character(unified_sent_layers,local_depth_argument)

		return former_words + [generated_length]

	def generate_word(self,former_words,file_name):
		# Get the historic of words lengths

		words_length = [len(word) for word in former_words.split(" ") if word]

		# With it, generate a new length

		generated_length = self.generate_word_length(words_length,1)


		# Get the letter associated with it 

		raw_probabilites = self.word_ends_probability_table[generated_length[-1]][0]

		length_intervals = self.create_probabilities_intervals(raw_probabilites)

		generated_beginning = self.get_char(self.draw_element(sum(raw_probabilites),length_intervals))

		# If the word is enough long, enforce an end

		raw_probabilites = self.word_ends_probability_table[generated_length[-1]][1]

		length_intervals = self.create_probabilities_intervals(raw_probabilites)

		generated_end = self.get_char(self.draw_element(sum(raw_probabilites),length_intervals))
		unknown_letter = generated_length[-1]-2

		if generated_length[-1] < 4:
			generated_end = "_"
			unknown_letter += 1

		#generated_end = ["er","ir","s","ux","el","sque"][random.randint(0,5)] if generated_length[-1] > 2 else "_"

		generated_end = "er"  if generated_length[-1] > 2 else "_"

		# Generate a word 

		word_to_generate = generated_beginning + unknown_letter*"_"+generated_end+"!"


		word = self.generate_gapped_text(1,file_name,word_to_generate,"0",generated_length[-1]-1,False)


		return former_words + word[0].lower()

	def generate_sentence(self,sentence_seed,word_count,file_name):
		sentence = sentence_seed
		for enumeration in range(word_count):
			sentence = self.generate_word(sentence,file_name)
			if not random.randint(0,12):
				add_char =  [",","."][random.randint(0,1)]
				if sentence[-2] != ",":
					sentence = sentence[:-1]+add_char+" "

		return sentence

	#- Specifications

	def initialize_generation(self,file_name,depth,space_factors,depth_factors):
		self.file_name = file_name
		self.depth_argument = depth
		self.space_factors = space_factors
		self.depth_factors = depth_factors

		if file_name != "random":
			self.initialize()
	
	def conclude_generation(self,saved_strings,total_repetitions):
		# Remove the duplicated elements 
		saved_strings = list(set(saved_strings))

		saved_strings.sort()

		ratio = round(len(saved_strings)/total_repetitions,2)

		# If it's verbose display the summary

		
		if self.verbose :
			print("===================================")
			print("---=== Results ===---")
			print("Words created : "+ str(total_repetitions)+" | Unique words : "+str(len(saved_strings))+" | Ratio : "+str(ratio))
			print("[Words generated]")
			print("• "+", ".join(saved_strings)+" •")
		return saved_strings

	def get_sent_ambidextrous_layers(self,table,text,subject_index,depth_argument,lettered):
		sent_layers = []
		development_length = len(text)

		for layer in range(1,depth_argument+1):
			# Add it to the layers
			forward_priority_table = self.get_sent_probability_table(table,text,layer,subject_index,development_length,True,lettered)[0]
			backward_priority_table = self.get_sent_probability_table(table,text,layer,subject_index,development_length,False,lettered)[0]

			sent_layers.append([forward_priority_table,backward_priority_table])
		
		return sent_layers

	def get_sent_probability_table(self,table,text,index,subject_index,text_length,forward,lettered):
		blank_layer = [0 for j in range(len(table))]

		object_index = subject_index + index*(-1)**forward 

		if object_index >= text_length or object_index < 0:
			#print("Letter that should help is out of the limits")
			return blank_layer,"!"


		# Get the letter
		current_sent_letter = text[object_index]

		
		# If it isn't guessed yet return blank layer
		if current_sent_letter == self.unknown_char:
			#print("The letter that should help is unknown") 
			return blank_layer,"!"

		# Else should return its probability table

		current_sent_index = self.get_id(current_sent_letter,lettered)


		return table[current_sent_index][not forward][index-1],current_sent_letter

	def stop_generate_string(self,text,stop_at,generated_character_count,max_character):
		if self.is_end_of_word(text,stop_at) or generated_character_count > max_character:
			return True 

	def filter_string(self,generated_string,searching,break_one):
		if searching == ["-"]: return True 

		if self.is_end_of_word(generated_string,searching):
			return True

	def get_first_gap(self,word):
		if self.unknown_char in word:
			return word.index(self.unknown_char)

#==- Conjugation -==#

	def conjugate(self,verb,person):
		for conjugations in list(self.conjugate_dict.keys()):
			if verb[-len(conjugations):] == conjugations:
				if conjugations == "ir" and verb[-3] == "o": continue
				verb = verb[:len(verb)-len(conjugations)] + self.conjugate_dict[conjugations][person]


		return verb.lower()
	
	def create_conjugation(self):


		self.conjugate_dict = {
			"er":["e","es","e","ons","ez","ent"],
			"ir":["is","is","it","issons","issez","issent"],
			"oir":["ois","ois","oit","oyons","oyez","oient"],
			"endre":["ends","ends","end","enons","enez","ennent"],
			}
	
	def generate_noun(self,seed,gender,plural):
		articles = [[
		["le","la","l'"],
		["un","une"],
		["ce","cette","cet "]],

		[["les"],["des"],["ces"],
		]]
		
		nouns = [
		["et","ette"],
		["on"],
		["eur","euse"],
		["tre"],
		["atre"],
		["ise"],
		["er","ere"],
		["ard","arde"],
		["el","elle"],
		["al"]]

		

		draw_noun_index = random.randint(0,len(nouns)-1)
		draw_noun = nouns[draw_noun_index][gender%len(nouns[draw_noun_index])]

		generated_noun = self.generate_gapped_text(1,"Texts/LC.txt",seed,draw_noun,4)[0].lower() + plural*"s"

		if generated_noun[-3:] == "als":
			generated_noun = generated_noun[:-3] + "aux"

		draw_article_index = random.randint(0,len(articles[plural])-1)
		draw_article = articles[plural][draw_article_index]
		generated_article = self.capitalize(draw_article[gender%len(draw_article)],0) + " "


		if not plural and generated_article[-2] in self.vowels and generated_noun[0] in self.vowels:
			if len(articles[0][draw_article_index]) > 2:
				generated_article = self.capitalize(articles[0][draw_article_index][2],0)

		return generated_article + generated_noun

	def generate_adverb(self,seed):
		return self.generate_gapped_text(1,"Texts/LC.txt",seed,"ement",4)[0].lower()

	def generate_pseudo_sentences(self):
		persons = [["Je"],["Tu"],["Il","Elle","On"],["Nous"],["Vous"],["Ils","Elles"]]
		verbs = ["er","air","oir","endre"]
		
		seed = "p"

		plural = random.randint(0,1)
		gender = random.randint(0,1)


		current_person_index = random.randint(0,2) + plural*3
		nounded = current_person_index == 2 and random.randint(1,10) > 3
		adverbed = random.randint(1,10) > 7

		current_person = persons[current_person_index][random.randint(0,len(persons[current_person_index])-1)] + " "
		
		generated_verb = self.generate_gapped_text(1,"Texts/LC.txt",seed,verbs[random.randint(0,len(verbs)-1)],4)[0]

		generated_adverb = ""

		if nounded:
			current_person =  self.generate_noun(seed,gender,plural) + " "

		if generated_verb[0].lower() in self.vowels and not current_person_index:
			current_person = "J'"
			
		if adverbed:
			generated_adverb = self.generate_adverb(seed)+" "

		conjugated_generated_verb = self.conjugate(generated_verb,current_person_index)

		print(current_person+conjugated_generated_verb+" "+generated_adverb+self.generate_noun(seed,random.randint(0,1),random.randint(0,1)).lower())

#==- Data collection -==#

	def extract_data(self,text):
		text = text.replace(".","")
		words = text.split(" ")
		word_count = len(words)
		word_lengths = []

		for i in range(word_count):
			word_lengths.append(len(words[i]))

		average_length = sum(word_lengths)/word_count
		return average_length

	def collect_data(self,file_name):
		value_test_size = 50
		sample_size = 160
		sample_results = []
		self.penultimate_factor = 1

		self.file_name = file_name
		self.initialize()

		for k in range(value_test_size):
			sample_results = []
			self.create_probability_table()
			self.set_probabilities()
			for i in range(sample_size):
				sample_results.append(self.extract_data(self.generate_text("L",1200)))
				
			average_length = sum(sample_results)/sample_size
			self.words_lengths_data.append(average_length/self.initial_word_length)
			self.initial_conditions_data.append(1+k)

			self.space_factor += 1

