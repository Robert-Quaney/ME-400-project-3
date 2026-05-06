import os #required for os.system("cls")
import csv #required to process csv file.
import datetime as dt
import matplotlib.pyplot as plt #required for plotting
import matplotlib.animation as animation
import numpy as np #required to convert to numerical array
from connector import OBDConnector #required to include OBDConnector class

# Helper functions

def ClearScreen():
    os.system("cls" if os.name == "nt" else "clear")

def MakeHex2(value):
    value = value.strip()
    value = value.upper()

    if len(value) == 0:
        value = "00"
    elif len(value) == 1:
        value = "0" + value

    return value


def IntToHex2(num):
    digits = "0123456789ABCDEF"

    first = num // 16
    second = num % 16

    return digits[first] + digits[second]


def inLists(mylist, value):
    for i in range(len(mylist)):
        if mylist[i] == value:
            return True

    return False


def FindPID(pid_codes, pid):
    for i in range(len(pid_codes)):
        if pid_codes[i] == pid:
            return i

    return -1


def PIDData():
    pid_codes = []
    descriptions = []
    units = []

    try:
        myfile = open("piddata.csv", "r", encoding="latin-1")
        data = csv.reader(myfile)

        row_count = 0

        for row in data:
            if row_count > 0:
                mode = MakeHex2(row[0])
                pid = MakeHex2(row[1])

                code = mode + pid

                pid_codes.append(code)
                descriptions.append(row[3].strip())
                units.append(row[6].strip())

            row_count = row_count + 1

        myfile.close()

    except:
        print("Unable to open piddata.csv")

    return pid_codes, descriptions, units


def CleanHexResp(response):
    response = response.replace(" ", "")
    response = response.strip()

    # response should look something like 4100XXXXXXXX
    # remove the 4100 part and keep the 8 data characters
    if len(response) >= 12:
        return response[4:12]

    return ""


def HexDigToBinary(ch):
    if ch == "0":
        return "0000"
    elif ch == "1":
        return "0001"
    elif ch == "2":
        return "0010"
    elif ch == "3":
        return "0011"
    elif ch == "4":
        return "0100"
    elif ch == "5":
        return "0101"
    elif ch == "6":
        return "0110"
    elif ch == "7":
        return "0111"
    elif ch == "8":
        return "1000"
    elif ch == "9":
        return "1001"
    elif ch == "A":
        return "1010"
    elif ch == "B":
        return "1011"
    elif ch == "C":
        return "1100"
    elif ch == "D":
        return "1101"
    elif ch == "E":
        return "1110"
    elif ch == "F":
        return "1111"
    else:
        return "0000"

def DecodePID(pid, response, formula):
    resp = response.replace(" ", "")

    # Extract bytes (A, B, C, D...)
    bytes_data = []
    for i in range(4, len(resp), 2):
        byte = int(resp[i:i+2], 16)
        bytes_data.append(byte)

    # Map variables A, B, C, D
    variables = {}
    for i, val in enumerate(bytes_data):
        variables[chr(ord('A') + i)] = val

    try:
        # Evaluate formula safely
        result = eval(formula, {}, variables)
        return round(result, 2)
    except:
        return response

def HexToBinary(hex_value):
    binary = ""

    for i in range(len(hex_value)):
        binary = binary + HexDigToBinary(hex_value[i])

    while len(binary) < 32:
        binary = "0" + binary

    if len(binary) > 32:
        binary = binary[0:32]

    return binary


def CleanBinaryResp(response, length):
    bits = ""

    for i in range(len(response)):
        ch = response[i]

        if ch == "0" or ch == "1":
            bits = bits + ch

    while len(bits) < length:
        bits = bits + "0"

    return bits[0:length]


def PIDtoList(pid_list, pid):
    if inLists(pid_list, pid) == False:
        pid_list.append(pid)


def EnabledPIDs():
    enabled = []

    commands = ["0100", "0120", "0140", "0160", "0900"]
    modes = ["01", "01", "01", "01", "09"]
    start_pids = [1, 33, 65, 97, 1]

    for block in range(len(commands)):
        resp = e.getPIDsingle(commands[block])

        hex_data = CleanHexResp(resp)
        bin_data = HexToBinary(hex_data)

        for i in range(32):
            if bin_data[i] == "1":
                pid_num = start_pids[block] + i
                pid_code = modes[block] + IntToHex2(pid_num)

                PIDtoList(enabled, pid_code)

    return enabled


def NormPIDs():
    normalized = []

    # PIDN gives normalized mode 01 PIDs
    pidn = e.getPIDsingle("PIDN")
    pidn = CleanBinaryResp(pidn, 128)

    for i in range(128):
        if pidn[i] == "1":
            pid_num = i + 1
            pid_code = "01" + IntToHex2(pid_num)

            PIDtoList(normalized, pid_code)

    # PIEN gives normalized mode 09 PIDs
    pien = e.getPIDsingle("PIEN")
    pien = CleanBinaryResp(pien, 132)

    for i in range(132):
        if pien[i] == "1":
            pid_num = i + 1
            pid_code = "09" + IntToHex2(pid_num)

            PIDtoList(normalized, pid_code)

    return normalized


# Option 3 helper functions

def CalcMPG(speed, maf):
    # speed should be vehicle speed from PID 010D
    # maf should be mass air flow from PID 0110

    try:
        speed = float(speed)
        maf = float(maf)

        if maf <= 0:
            return 0.0

        mpg = 710.7 * speed / maf
        return mpg

    except:
        return 0.0


def PlotMPGData():
    ClearScreen()

    print("Graphing MPG Data")
    print("Close the graph window to return to the main menu.")

    xs.clear()
    ys.clear()

    # Add a plot to the figure.
    fig = plt.figure()

    ax = fig.add_subplot(1, 1, 1)

    # Set up plot to call AnimateMPG function periodically
    ani = animation.FuncAnimation(fig, AnimateMPG, fargs=(fig, ax, xs, ys), interval=1000)

    plt.show()


def AnimateMPG(i, fig, ax, xs, ys):
    # Read speed data from PID 010D
    speed = e.getPIDsingle("010D")

    # Read mass air flow data from PID 0110
    maf = e.getPIDsingle("0110")

    mpg = CalcMPG(speed, maf)

    # Add x and y data to lists
    xs.append(dt.datetime.now().strftime("%M:%S"))
    ys.append(mpg)

    # Limit x and y lists to 20 items
    xs = xs[-20:]
    ys = ys[-20:]

    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys)

    # Rescale the graph
    ax.relim()
    ax.autoscale_view()

    # Format plot
    plt.xticks(rotation=45, ha="right")
    plt.subplots_adjust(bottom=0.30)
    plt.title("MPG VERSUS TIME")
    plt.xlabel("Time")
    plt.ylabel("PID DATA Miles Per Gallon")
    plt.grid(True)

    print("Speed =", speed, "MAF =", maf, "MPG =", mpg)


# Main menu function

def MainMenu():
    ClearScreen()

    print("1.  Query PID Data")
    print("2.  Graph PID Data")
    print("3.  Graph MPG Data")
    print("4.  Exit Program")
    selection = input("Input your selection...")
    return selection


#
#   Begin main program
#

# Setup some global lists to use for mpg real time plotting.
xs = []
ys = []

# Create instance of the OBDConnector object.
e = OBDConnector(False)

# Connect to the Arduino
e.connect()

# Initialize the main menu selection.
selection = 0

# Loop until user exits
while (selection != "4"):
    # Get menu selection from user.
    selection = MainMenu()

    # Branch based on user selection.

    ## BEGIN SECTIOIN 1///////////////////////////////////////////////////////////////////////////////////////////
    if (selection == "1"):
       # a. clear screen
        ClearScreen()
        # Create menu listing of PIDS based on
        # contents of piddata.csv.  Disable options
        # that are not enabled for connected
        # vehicle.  Display PID data for option
        # selected by user.
        #
         # b. read PID data
        pid_dict = {}

        with open('piddata.csv', mode='r') as myfile:
            reader = csv.reader(myfile)
            next(reader)

            for row in reader:
                mode = MakeHex2(row[0])
                pid = MakeHex2(row[1])
                code = mode + pid

                pid_dict[code] = {"descrpt": row[3].strip(), "units": row[6].strip(),"formula": row[7].strip()}

        enabled_pids = EnabledPIDs()

        special_pids = ["0100", "0120", "0140", "0160", "0900"]
        for sp in special_pids:
            if sp not in enabled_pids:
                enabled_pids.append(sp)

        # Display menu
        for hex_code in sorted(pid_dict.keys()):
            if hex_code in enabled_pids:
                info = pid_dict[hex_code]
                units = info['units'] if info['units'] else ""
                print(f"{hex_code} - {info['descrpt']} ({units})")

    # User input
        user_enter = input("\nEnter 4 digit HEX code: ").upper()

        if user_enter in enabled_pids and user_enter in pid_dict:
            data = e.getPIDsingle(user_enter)
            units = pid_dict[user_enter]['units']

            formula = pid_dict[user_enter]["formula"]
            decoded = DecodePID(user_enter, data, formula)
            print(f"\nPID DATA FOR {user_enter} = {decoded} {units}")
        else:
            print("\nError: Invalid PID")

        input("\nPress any key to return to the main menu")

        ## BEGIN SECTIOIN 2//////////////////////////////////////////////////////////////////////////////////////

    elif (selection == "2"):
        ClearScreen()

        print("Loading PID data...\n")
        pid_dict = {}

        with open('piddata.csv', mode='r', encoding="latin-1") as myfile:
            reader = csv.reader(myfile)
            next(reader)

            for row in reader:
                mode = MakeHex2(row[0])
                pid = MakeHex2(row[1])
                code = mode + pid

                pid_dict[code] = {
                    "descrpt": row[3].strip(),
                    "units": row[6].strip(),
                    "formula": row[7].strip()
                }
        enabled_pids = EnabledPIDs()

        # ensure required blocks exist
        for sp in ["0100", "0120", "0140", "0160", "0900"]:
            if sp not in enabled_pids:
                enabled_pids.append(sp)


        normalized_pids = []

        # PIDN (01xx range)
        pidn = e.getPIDsingle("PIDN")
        pidn = CleanBinaryResp(pidn, 128)

        for i in range(128):
            if pidn[i] == "1":
                pid_code = "01" + IntToHex2(i + 1)
                PIDtoList(normalized_pids, pid_code)

        # PIEN (09xx range)
        pien = e.getPIDsingle("PIEN")
        pien = CleanBinaryResp(pien, 132)

        for i in range(132):
            if pien[i] == "1":
                pid_code = "09" + IntToHex2(i + 1)
                PIDtoList(normalized_pids, pid_code)

  
        graphable_pids = []

        for code in pid_dict.keys():
            if code in enabled_pids and code in normalized_pids:
                graphable_pids.append(code)

        graphable_pids.sort()


        print("AVAILABLE PIDS\n")

        for code in graphable_pids:
            info = pid_dict[code]
            units = info["units"] if info["units"] else ""
            print(f"{code} - {info['descrpt']} ({units})")


        pid_choice = input("\nEnter 4-digit HEX PID code: ").strip().upper()

        if pid_choice in graphable_pids and pid_choice in pid_dict:
            tdat, pdat = e.getPIDmultiple(pid_choice, 60, 1000)

            tdat = np.array(tdat, dtype=np.float32)
            pdat = np.array(pdat, dtype=np.float32)

            info = pid_dict[pid_choice]
            units = info["units"]

            plt.figure()
            plt.scatter(tdat, pdat, marker="o", label="pid data")

            plt.title(f"PID DATA FOR {pid_choice}")
            plt.xlabel("time (ms)")
            plt.ylabel(f"PID DATA ({units})")

            plt.grid(True)
            plt.legend(loc="upper left")

            plt.show()

        else:
            print("\nInvalid or unavailable PID selected.")

        input("\nPress Enter to return to main menu...")

    ## BEGIN SECTIOIN 3/////////////////////////////////////////////////////////////////////////////////////
    elif (selection == "3"):
        PlotMPGData()

        input("Press any key to continue")

# Close the OBDConnector object
e.close()