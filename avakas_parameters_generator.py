import numpy as np
import pickle
from datetime import datetime 
from os import path, mkdir
import shutil
from collections import OrderedDict
import re


def date():

    return str(datetime.now())[:-10].replace(" ", "_").replace(":", "-")


class ParametersGenerator(object):

    def __init__(self):

        self.t_max = 5000

        self.model_parameters = "economics-model-parameters.json"
        # self.hebbian = False
        self.reward_amount = 1

        self.n_cpu = 12

        self.date = date()

        self.folders = OrderedDict(
            [
                ("macro", "server"),
                ("scripts", "../avakas_scripts"),
                ("parameters", "../avakas_input_parameters"),
                ("logs", "../avakas_logs"),
                ("data", "../data")
            ]
        )

        self.nb_sub_list = 168

    def empty_scripts_folder(self):

        if path.exists(self.folders["data"]):

            response = input("Do you want to remove data folder?")

            while response not in ['y', 'yes', 'n', 'no', 'Y', 'N']:
                response = input("You can only respond by 'yes' or 'no'.")

            print("Proceeding...")

            if response in ['y', 'yes', 'Y']:

                if path.exists(self.folders["data"]):
                    shutil.rmtree(self.folders["data"])
                print("Data folder has been erased.")
            else:
                print("Data folder has been conserved.")

        else:
            print("Proceeding...")

        print("Remove old scripts and logs...")

        if path.exists(self.folders["scripts"]):

            shutil.rmtree(self.folders["scripts"])

        print("Old scripts and logs have been removed.")

        if path.exists(self.folders["logs"]):

            shutil.rmtree(self.folders["logs"])

    def create_folders(self):

        for directory in self.folders.values():

            if not path.exists(directory):
                mkdir(directory)

    @classmethod
    def generate_workforce_list(cls):

        workforce_list = list()
        workforce = np.zeros(3, dtype=int)

        workforce_step = 25
        workforce_mini = 50
        workforce_maxi = 200

        workforce[:] = workforce_mini

        possible_w = np.arange(workforce_mini, workforce_maxi+0.1, workforce_step)

        # for i in possible_w:
        #     workforce[2] = i
        #     workforce_list.append(workforce.copy())

        for i in possible_w:
            for j in possible_w:
                for k in possible_w:
                    if i <= j <= k:
                        workforce[:] = i, j, k
                        workforce_list.append(workforce.copy())

        print("Length of workforce list:", len(workforce_list))
        return workforce_list

    def generate_parameters_list(self, workforce_list):

        idx = 0
        parameters_list = []

        for workforce in workforce_list:

            for hebbian in [0, 1]:

                parameters = \
                    {
                        "workforce": workforce,
                        "t_max": self.t_max,  # Set the number of time units the simulation will run
                        "model": "BG",
                        "model_parameters": self.model_parameters,
                        "hebbian": hebbian,
                        "reward_amount": self.reward_amount,
                        "cpu_count": self.n_cpu,
                        "idx": idx,  # For saving
                        "date": self.date  # For saving

                    }
                parameters_list.append(parameters)
                # increment idx
                idx += 1

        return parameters_list

    def generate_input_parameters(self, parameters_list):

        len_sub_part = len(parameters_list) / self.nb_sub_list
        rounded_len_sub_part = int(len_sub_part)

        # If there is more tasks than jobs...

        if len_sub_part > 1:

            input_parameters_dict = {}  # Keys will be the ID of the script to be executed

            cursor = 0

            for i in range(self.nb_sub_list):

                part = parameters_list[cursor:cursor + rounded_len_sub_part]
                input_parameters_dict[i] = part
                cursor += rounded_len_sub_part

            while cursor < len(parameters_list):

                for i in range(self.nb_sub_list):

                    if cursor < len(parameters_list):
                        input_parameters_dict[i].append(parameters_list[cursor])
                        cursor += 1

        # If there is an equal number of tasks and jobs, or less...
        else:

            len_sub_part = 1
            self.nb_sub_list = len(parameters_list)

            input_parameters_dict = {}
            for i in range(self.nb_sub_list):

                # Input parameters for a job is a list containing a unique element
                input_parameters_dict[i] = [parameters_list[i]]

        return input_parameters_dict, len_sub_part

    def save_input_parameters(self, input_parameters):

        print("Save input parameters...")
        
        for i in range(len(input_parameters)):

            pickle.dump(input_parameters[i],
                        open("{}/slice_{}.p".format(self.folders["parameters"], i), mode="wb"))

        print("Input parameters saved.")

    def create_scripts(self):

        print("Create scripts...")

        root_file = "{}/simulation.sh".format(self.folders["macro"])
        prefix_output_file = "{}/ecoBGModel-simulation_".format(self.folders["scripts"])

        for i in range(self.nb_sub_list):
            f = open(root_file, 'r')
            content = f.read()
            f.close()

            replaced = re.sub('slice_0', 'slice_{}'.format(i), content)
            replaced = re.sub('ecoBGModel-simulation_0', 'ecoBGModel-simulation_{}'.format(i), replaced)

            script_name = "{}{}.sh".format(prefix_output_file, i)

            f = open(script_name, 'w')
            f.write(replaced)
            f.close()

        print("Scripts created.")
    
    def run(self):

        workforce_list = self.generate_workforce_list()
        parameters_list = self.generate_parameters_list(workforce_list=workforce_list)
        input_parameters, len_sub_part = self.generate_input_parameters(parameters_list)

        response = input("Number of jobs: {}; number of tasks per job: {}; "
                         "total number of tasks: {}. \n"
                         "Should I proceed?".format(self.nb_sub_list, len_sub_part,
                                                    len(parameters_list)))
        while response not in ['y', 'yes', 'n', 'no', 'Y', 'N']:
            response = input("You can only respond by 'yes' or 'no'.")

        if response in ['y', 'yes', 'Y']:

            self.empty_scripts_folder()
            self.create_folders()
            self.save_input_parameters(input_parameters)
            self.create_scripts()
            # self.create_meta_launcher()

            print("Done!")

        else:
            print("Process aborted by user.")


def main():

    p = ParametersGenerator()
    p.run()
                        
if __name__ == "__main__":

    main()

