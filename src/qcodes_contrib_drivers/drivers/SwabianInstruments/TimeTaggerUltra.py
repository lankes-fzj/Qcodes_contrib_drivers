# -*- coding: utf-8 -*-
"""
QCoDeS-Driver for the Swiabian Instruments Time Tagger Ultra.

Authors:
    Kardynal, Beata (Forschungszentrum Jülich GmbH - PGI-9) <b.kardynal@fz-juelich.de>
    Lankes, Lukas (Forschungszentrum Jülich, IBI-TAE) <l.lankes@fz-juelich.de>
"""
import time
import typing

import matplotlib.pyplot as plt
import qcodes as qc
import qcodes.utils.validators as vals

try:
    import TimeTagger as tt
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError("Please install the TimeTagger library to use the TimeTaggerUltra " +
                              "Qcodes-instrument!") from exc


class TTUChannel(qc.InstrumentChannel):
    """
    Channel class for the Time Tagger Ultra.

    Args:
        parent: The parent TTUltra instrument.
        name: Name to assign to the channel.
        channel: The channel number.
    """

    def __init__(self, parent: "TTUltra", name: str, channel: int):
        super().__init__(parent, name)

        # validate the channel value
        self.channel = channel

        # Parameters
        self.add_parameter("TriggerLevel",
         	               get_cmd=self._get_triggerlevel,
                           set_cmd=self._set_triggerlevel,
             	           unit="V",
                           vals=vals.Numbers(),
                           docstring="Trigger level of an input channel.")
        self.add_parameter("TestSignal",
                           get_cmd=self._get_testsignal,
                           set_cmd=self._set_testsignal,
                           vals=vals.Bool(),
                           docstring="Test signal of internal signal generator")

    def _get_triggerlevel(self) -> float:
        return self._parent.tagger.getTriggerLevel(self.channel)

    def _set_triggerlevel(self, level: float) -> None:
        self._parent.tagger.setTriggerLevel(self.channel,level)

    def _get_testsignal(self) -> bool:
        return self._parent.tagger.getTestSignal(self.channel)

    def _set_testsignal(self, state: bool) -> None:
        self._parent.tagger.setTestSignal(self.channel, state)


class TTUltra(qc.Instrument):
    """Instrument class for Swabian Instruments Time Tagger Ultra
    
    Args:
        name: Unique name of the instrument
        serial_number (optional): Serial number of the device to connect to.
    """

    def __init__(self, name: str, serial_number: str = "", **kwargs):
        super().__init__(name, **kwargs)

        # Create driver instance
        self.tagger = tt.createTimeTagger(serial_number)

        # Get device information
        self.version= tt.getVersion()
        self.serial= self.tagger.getSerial()
        self.model = self.tagger.getModel()

        # Get available channels
        self.channels = qc.ChannelList(self, "TTUChannel", TTUChannel)
        channels = self.tagger.getChannelList(tt.ChannelEdge.All)

        # Create and add Qcodes-instrument-channels
        for ch in channels:
            ch_name = f"ch_{ch}" if ch >= 0 else f"ch_m{abs(ch)}"
            channel = TTUChannel(self, ch_name, ch)
            self.channels.append(channel)
            self.add_submodule(ch_name, channel)

        self.channels.lock()
        self.add_submodule("channels", self.channels)

        self.connect_message()

    def get_idn(self) -> typing.Dict[str, typing.Optional[str]]:
        """
        Returns a dictionary with information about the device

        Returns:
            A dictionary containing vendor, model, serial number and firmware version
        """
        return {"vendor": "Swabian Instruments", "model": self.model,
                "serial": self.serial, "firmware": self.version}

    def measure_to_file(self, filepath: str, duration: float):
        """Start measurement and store recorded data to file(s).

        Args:
            filepath (str): Path to the first file (possible additional files are named
                            accordingly).
            duration (float): Duration of recording in seconds (s).
        """
        synchronized = tt.SynchronizedMeasurements(self.tagger)
        filewriter = None

        try:
            # This FileWriter will not start automatically, it waits for 'synchronized'
            filewriter = tt.FileWriter(synchronized.getTagger(), filepath, [2,4])
            filewriter.setMaxFileSize(5 * 1024 * 1024)  # Maximum 5MiB per file
            print(filewriter)

            # Start measurement and wait for completion
            synchronized.startFor(int(duration * 1e12))
            synchronized.waitUntilFinished()

            # Print summary
            number_of_events = filewriter.getTotalEvents()
            file_size = filewriter.getTotalSize()
            print(f"{number_of_events} were written to file. Storing required " +
                  f"{file_size/number_of_events:.3f} bytes/tag.")
        finally:
            # Cleanup
            if filewriter is not None:
                del filewriter
            del synchronized

    def read_measurement_files(self, filepath: str, chunk_size: int = 100000,
            callback: typing.Callable[[tt.TimeTagStreamBuffer], None] = None):
        """Reads file(s) with recorded measurements.

        Args:
            filepath (str): File to read from.
            chunk_size (int, optional): Number of events to read at once (defaults to 100000).
            callback (callable, optional): Callback function to call when data was read.
        """
        filereader = tt.FileReader(filepath)

        # Table format
        FMT_STR = "{:>8} | {:>17} | {:>7} | {:>14} | {:>13}"

        try:
            # The format for the table and the head of the table
            print(FMT_STR.format("TAG #", "EVENT TYPE", "CHANNEL", "TIMESTAMP (ps)",
                                 "MISSED EVENTS"))
            print("---------+-------------------+---------+----------------+--------------")
            line_length = 71

            event_name = ["0 (TimeTag)", "1 (Error)", "2 (OverflowBegin)", "3 (OverflowEnd)",
                          "4 (MissedEvents)"]

            i = 0
            while filereader.hasData():
                # getData() does not return timestamps, but an instance of TimeTagStreamBuffer
                # that contains more information than just the timestamp
                data = filereader.getData(n_events=chunk_size)

                if callback:
                    callback(data)

                # With the following methods, we can retrieve a numpy array for the particular
                # information:
                channels = data.getChannels()  # The channel numbers
                timestamps = data.getTimestamps()  # The timestamps in ps
                event_types = data.getEventTypes()  # Type of event (see `event_name`)
                missed_events = data.getMissedEvents()  # The numbers of missed events in case of
                                                        # overflow

                # Output to table
                if i < 2 or not filereader.hasData():
                    # Print heading (and empty lines)
                    print(FMT_STR.format("", "", "", "", ""))
                    heading = f"Start of data chunk {i + 1} with {data.size} events"
                    print(f" {heading} ".center(line_length))
                    print(FMT_STR.format("", "", "", "", ""))

                    # Print first event
                    print(FMT_STR.format(
                        i*chunk_size + 1, event_name[event_types[0]],
                        channels[0], timestamps[0], missed_events[0]))
                    # Print second event
                    if data.size > 1:
                        print(FMT_STR.format(
                            i*chunk_size + 2, event_name[event_types[1]],
                            channels[1], timestamps[1], missed_events[1]))
                    # Print ellipses
                    if data.size > 3:
                        print(FMT_STR.format("...", "...", "...", "...", "..."))
                    # Print last event
                    if data.size > 2:
                        print(FMT_STR.format(
                            i*chunk_size + data.size, event_name[event_types[-1]],
                            channels[-1], timestamps[-1], missed_events[-1]))

                # Print empty line and vertical ellipses
                if i == 1:
                    print(FMT_STR.format("", "", "", "", ""))
                    for _ in range(3):
                        print(FMT_STR.format(".", ".", ".", ".", "."))

                i += 1
        finally:
            # Close the FileReader and remove the temporary files
            del filereader

    def counter(self, channel: int, wait_time: float,
                bin_width: int = int(1e9), bin_count: int = 1000):
        """Plots the event count for a channel

        Args:
            channel (int): Channels where to count the events.
            wait_time (float): Time to wait before requesting the data in seconds (s).
            bin_width (int, optional): Bin width in picoseconds (ps). Defaults to 1e9 (1 ms).
            bin_count (int, optional): Number of bins (data buffer size). Defaults to 1000.
        """
        # The channel to be measured has to have the TestSignal set to "False" in the QCodes script
        counter = tt.Counter(self.tagger, [channel], bin_width, bin_count)

        # Wait before getting data
        time.sleep(wait_time)
        data = counter.getData()

        # Plot the result
        plt.figure()
        plt.plot(counter.getIndex() / 1e12, data[0] * 1e-3, label=f"Channel {channel}")
        plt.xlabel("Time [s]")
        plt.ylabel("Countrate [MHz]")
        plt.legend()
        plt.title(f"Time trace of the click rate on channel {channel}")
