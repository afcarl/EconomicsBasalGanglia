import numpy as np
import pickle
from datetime import datetime 
from os import path, mkdir, popen
from collections import OrderedDict
import re


def date():

    return str(datetime.now())[:-10].replace(" ", "_").replace(":", "-")


class ParametersGenerator(object):

    def __init__(self):

        self.alpha_list = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.tau_list = [0.01, 0.02, 0.03, 0.04, 0.05]
        self.vision_list = [1, 3, 6, 12, 15]
        self.area_list = [1, 3, 6, 12, 15]

        self.stride = 1
        self.t_max = 600
        self.width = 30
        self.height = 30

        self.workforce_step = 10
        self.workforce_mini = 50
        self.workforce_maxi = 100
    
        self.date = date()

        root_folder = "../data"

        self.folders = OrderedDict(
            [
                ("macro", "server"),
                ("root", root_folder),
                ("parameters", "{}/input_parameters".format(root_folder)),
                ("session", "{}/session".format(root_folder)),
                ("scripts", "{}/scripts".format(root_folder))
            ]
        )

        self.nb_sub_list = None

    def empty_scripts_folder(self):

        if path.exists(self.folders["scripts"]):

            popen("rm -r -f {}".format(self.folders["scripts"]))

    def create_folders(self):

        for directory in self.folders.values():

            if not path.exists(directory):
                mkdir(directory)

    def generate_workforce_list(self):

        array = np.zeros(3)
        array[:] = self.workforce_mini

        workforce_list = list()

        possible_w = np.arange(self.workforce_mini, self.workforce_maxi+0.1, self.workforce_step)
        for i in possible_w:
            for j in possible_w:
                for k in possible_w:
                    if i <= j <= k:
                        array[:] = i, j, k
                        workforce_list.append(array.copy())

        print("Length of workforce list:", len(workforce_list))
        return workforce_list

    def generate_parameters_list(self, workforce_list):

        idx = 0
        parameters_list = []
        suffixes_list = [] 

        for workforce in workforce_list:

            parameters = \
                {
                    "workforce": np.array(workforce, dtype=int),
                    "t_max": self.t_max,  # Set the number of time units the simulation will run
                    "model": "BG",
                    "cpu_count": 12,
                    "idx": idx,  # For saving
                    "date": self.date  # For saving

                }
            parameters_list.append(parameters)
            suffixes_list.append("{date}_idx{idx}".format(date=self.date, idx=idx))

            # increment idx
            idx += 1

        return parameters_list, suffixes_list

    def save_parameters_list(self, parameters_list, suffixes_list):

        print("Save input parameters...")
        
        for i, parameters in enumerate(parameters_list):

            pickle.dump(parameters,
                        open("{}/slice_{}.p".format(self.folders["parameters"], i), mode="wb"))

        pickle.dump(suffixes_list,  open("{}/session_{}.p".format(self.folders["session"], self.date), mode="wb"))

        print("Input parameters saved.")

    def create_scripts(self):

        print("Create scripts...")

        root_file = "{}/simulation.sh".format(self.folders["macro"])
        prefix_output_file = "{}/ecoBG-simulation_".format(self.folders["scripts"])

        script_names = []

        for i in range(self.nb_sub_list):
            f = open(root_file, 'r')
            content = f.read()
            f.close()

            replaced = re.sub('slice_0', 'slice_{}'.format(i), content)
            replaced = re.sub('ecoBG-simulation_0', 'ecoBG-simulation_{}'.format(i), replaced)

            script_name = "{}{}.sh".format(prefix_output_file, i)

            f = open(script_name, 'w')
            f.write(replaced)
            f.close()

            script_names.append(script_name)

        print("Scripts created.")

        return script_names

    def create_meta_launcher(self, script_names):

        print("Create launch script...")

        pickle.dump(script_names,
                    open("{}/avakas_launcher_args.p".format(self.folders["scripts"]), mode='wb'))

        print("Script created.")
    
    def run(self):

        workforce_list = self.generate_workforce_list()
        parameters_list, suffixes_list = self.generate_parameters_list(workforce_list=workforce_list)
        self.nb_sub_list = len(parameters_list)

        response = input("Number of tasks: {}. Should I proceed?".format(self.nb_sub_list))
        while response not in ['y', 'yes', 'n', 'no', 'Y', 'N']:
            response = input("You can only respond by 'yes' or 'no'.\n"
                             "Number of tasks: {}. Should I proceed?".format(self.nb_sub_list))

        if response in ['y', 'yes', 'Y']:

            print("Proceeding...")

            self.empty_scripts_folder()
            self.create_folders()
            self.save_parameters_list(parameters_list, suffixes_list)
            script_names = self.create_scripts()
            self.create_meta_launcher(script_names)

            print("Done!")

        else:
            print("Process aborted by user.")


def main():

    p = ParametersGenerator()
    p.run()
                        
if __name__ == "__main__":

    main()
