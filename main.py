import gui
import sys 

#= Visual Interface =#

gui_instance = gui.GUI()
gui_instance.run()

#==== OR ====#

collapsed_text = api.wfca.CollapsedText(verbose=True)

# To generate words like "D [...] ed" do this

generated_result = collapsed_text.generate_spaced_text(enumerations=int(sys.argv[2]),
					file_name=sys.argv[1],
					start_seed=sys.argv[3],
					end_seed=sys.argv[4],
					filling=int(sys.argv[5]))

exit()
# To complete words like "C__pl_te" do this

generated_result = collapsed_text.generate_gapped_text(enumerations=int(sys.argv[2]),
					file_name=sys.argv[1],
					seed=sys.argv[3])
