#----------------------------| Importing Required modules |----------------------------
import tkinter as tk       
from tkinter import StringVar, messagebox
from tkinter.constants import S
import countryinfo, datetime, pytz, requests, webbrowser
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

#======================================================| Current Weather |========================================================
class CurrentWeather:
    
    _API = "YOUR_API_KEY"

    with open("./assets/unit.txt") as u:
        _unit = u.read()
    
    _UNITS = {  "C" : ["Celsius", "metric"],
            "F" : ["Fahreneit", "imperial"],
        }

    def get_weather(self, city : str) -> int:
        """Get current weather from Current Weather Data API and other details of provided city"""

        self.__city = city
        try:
            self.__current = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={self.__city}\
&appid={self._API}&units={self._UNITS[self._unit][1]}", timeout=15)

        except requests.exceptions.ConnectionError:     # No Internet
            return 1
        except requests.Timeout:                        # response time out
            return 2
        else:
            # converting current weather in json format
            self.__current_json = self.__current.json()
            try:
                self._lat = self.__current_json["coord"]["lat"]               # Latitude
                self._lon = self.__current_json["coord"]["lon"]               # Longitude
                return 0
            except KeyError:        # City name is not present
                return 3

    #----------------------------| Current Temperature |----------------------------
    def current_weather(self) -> tuple[int | float | str]:
        """Fetch following details from current weather
        return:
            (temp, temp_name, temp_des, humidity)
            temp        -> temperature
            feels       -> feels like
            temp_name   -> name of temperature
            temp_des    -> description of temperature
            humditiy    -> humidity
            visibility  -> visibility"""

        __temp = self.__current_json["main"]["temp"]                     # according to units
        __feels = self.__current_json["main"]["feels_like"]              # according to units
        __temp_name = self.__current_json["weather"][0]["main"]          # group of weather
        __temp_des = self.__current_json["weather"][0]["description"]    # group of weather
        __humidity = self.__current_json["main"]["humidity"]             # percent %
        __visible = self.__current_json["visibility"]                    # meters

        return (__temp, __feels, __temp_name, __temp_des, __humidity, __visible)


    #----------------------------| Location of City |----------------------------
    def location_details(self) -> tuple[float | str]:
        """Fetch information of user's provided location
        return:
            lat                 -> Latitude
            lon                 -> Longitude
            city                -> City name (official)
            con_code            -> Country code
            country_name        -> Country name
            region              -> Region of country
            time_zone           -> Time Zone
            zone_name           -> name of Time Zone"""

        __city_name = self.__current_json["name"]                    # City name
        __con_code = self.__current_json["sys"]["country"]           # Country code
        __country_name = pytz.country_names[__con_code]                 # Country name

        __country_info = countryinfo.CountryInfo(__country_name).info()
        __region = __country_info["region"]                             # Region name

        self.__zone_name = pytz.country_timezones[__con_code][0]        # Time zone name
        # self.__time_zone = self.__country_info["timezones"][0][3:]                      # Time zone
        __time_zone = datetime.datetime.now(tz=pytz.timezone(self.__zone_name)).strftime("%z")

        return (self._lat, self._lon, __city_name, __con_code, __country_name, __region, __time_zone, self.__zone_name)


    #----------------------------| Time of City |----------------------------
    def current_time(self) -> tuple[str]:
        """Fetch current time and current day of user's location
        return:
            current_time    -> Current Time
            current_Day:   -> Current Day"""

        # current time in HH : MM : SS  AM/PM 12-hr format
        __current_time = datetime.datetime.now(pytz.timezone(self.location_details()[-1])).strftime("%I:%M %p")
        __current_day = datetime.datetime.now(pytz.timezone(self.location_details()[-1])).strftime("%a, %d %b' %y")
        return (__current_time, __current_day)


#====================================================| 7-days Weather Forecast |====================================================
class WeekForecast(CurrentWeather):

    def get_forecast(self, city : str) -> int:
        """Fetch forecast from One Call API and other details of provided city
        first verify the location from get_weather() method of CurrentWeather class."""

        __exit_status = super().get_weather(city)
        if (__exit_status == 0):
            # Getting 7 day forecast from open weather API, of user's provided location's latitude & longitude
            self.__forecast = requests.get(f"https://api.openweathermap.org/data/2.5/onecall?lat={self._lat}&lon={self._lon}\
&appid={self._API}&units={self._UNITS[self._unit][1]}&exclude=minutely", timeout=15)

            # converting 7-day forecast into json format
            self._seven_days_weather = self.__forecast.json()
            return 0
        else:
            return __exit_status

    #--------------------------| Current Day Temperature |--------------------------
    def current_day_temps(self) -> dict[str : float]:
        """--------------------------| Current Day Temperature |--------------------------
        Fetch day, date and time of current day (24-hours - 3hr diff)
        -> returns a dictionary of time as key and temperature as value
        -> { time : day }
        return:
        ->     current_day_temp    -> Temperature of 24-hours of 3 hour difference """

        __current_day_temp = {}
        for __i, __hours in enumerate(self._seven_days_weather["hourly"]):
            if (__i > 24):  break
            if (__i%3==0):
                __day = datetime.datetime.fromtimestamp(__hours["dt"]).strftime("%d %B").split()
                __day[1] = __day[1][:3]
                __time = datetime.datetime.fromtimestamp(__hours["dt"]).strftime("%I:%M %p")
                __date = f"{__day[0]} {__day[1]}\n{__time}"

                __temp = __hours["temp"]

                __current_day_temp[__date] = __temp

        return __current_day_temp

    #------------------------------------Sunrise-and-Sunset----------------------------------------
    def current_sun_time(self) -> tuple[str]:
        """Get sunrise and sunset time of current day
        return:
            sunrise     -> Sunrise
            sunset      -> Sunset"""

        __sunrise = datetime.datetime.fromtimestamp(self._seven_days_weather["daily"][0]["sunrise"]).strftime("%I:%M %p")
        __sunset = datetime.datetime.fromtimestamp(self._seven_days_weather["daily"][0]["sunset"]).strftime("%I:%M %p")
        return (__sunrise, __sunset)

    #-----------------------------------Moonrise-and-Moonset---------------------------------------
    def current_moon_time(self) -> tuple[str]:
        """Get moonrise and moonset time of current day
        return:
            moonrise    -> Moonrise
            moonset     -> Moonset"""

        __moonrise = datetime.datetime.fromtimestamp(self._seven_days_weather["daily"][0]["moonrise"]).strftime("%I:%M %p")
        __moonset = datetime.datetime.fromtimestamp(self._seven_days_weather["daily"][0]["moonset"]).strftime("%I:%M %p")
        return (__moonrise, __moonset)

    #---------------------------------Current-Day-Min-Max-Temperature------------------------------
    def today_min_max_temp(self) -> tuple[float]:
        """Get minimum and maximum temperature of current day
        return:
            min_temp    -> Minimum temperature
            max_temp    -> Maximum temperature"""

        __min_temp = self._seven_days_weather["daily"][0]["temp"]["min"]
        __max_temp = self._seven_days_weather["daily"][0]["temp"]["max"]
        return (__min_temp, __max_temp)

    #---------------------------------------7-Day-Forecast-----------------------------------------
    def Seven_days_forecast(self) -> list[dict[str, int | float | str]]:
        """
        Get information of next 7 days each day info is stored in a dictionary manner
        { "Date" : date,        "Temp" : temp,         "Day:" : day_temp, 
         "Night:" : night_temp, "Name" : weather_name, "Description" : weather_des}
        return:
            days                -> list of 7-day forecast"""

        __week_temps = []
        for __day in self._seven_days_weather["daily"][1:]:

            __date = datetime.datetime.fromtimestamp(__day["dt"]).strftime("%d %b' %y")
            __temp = round(__day["temp"]["day"], 2)
            __day_temp = round(__day["temp"]["day"], 2)
            __night_temp = round(__day["temp"]["night"], 2)
            __weather_name = __day["weather"][0]["main"]
            __weather_des = __day["weather"][0]["description"]

            __day_set = {"Date" : __date, "Temp" : __temp, "Day:" : __day_temp,
            "Night:" : __night_temp, "Name" : __weather_name, "Description" : __weather_des}
            
            __week_temps.append(__day_set)
        
        return __week_temps


#====================================================| Initializes Tkinter Window |====================================================
class WeatherApp(tk.Tk, WeekForecast):

    start = True
    first_time = True
    state = "active"
    with  open("./assets/location.txt") as l:
        default_city = l.read()

    with open("./assets/view.txt") as v:
        default_view = v.read()
    view = default_view

    # images names : [weather name, weather description]
    weather_images = {
        "./assets/sunny.png" : ["Clear", "clear sky"],      # 01d, 01n

        "./assets/clear_sky.png" : ["Clouds", "few clouds"],      # 02d, 02n

        "./assets/cloudy.png" : ["Clouds", "scattered clouds", "broken clouds", "overcast clouds"],      # 03d, 03n, 04d, 04n

        "./assets/foggy.png" : ["Mist", "Smoke", "smoke", "Haze", "haze", "Fog", "mist", "fog"],     # 50d, 50n

        "./assets/snow.png" : ["Snow", "freezing rain", "light snow", "Heavy snow", "Steet", "Light shower sleet",
        "Shower sleet", "Light rain and snow", "Rain and snow", "Light shower snow", "Shower snow", "Heavy shower snow", "rain and snow"],    # 13d, 13n

        "./assets/windy.png" : ["Dust", "sand/ dust whirls", "Sand", "sand", "dust", "Ash", "Squall", "squalls", "Tornado", "tornado"],     # 50d, 50n

        "./assets/rainy.png" : ["Drizzle", "light intensity drizzle", "drizzle", "heavy intensity drizzle",
        "light intensity drizzle rain", "drizzle rain", "heavy intensity drizzle rain", "shower rain and drizzle",
        "heavy shower rain and drizzle", "shower drizzle", "Rain", "light rain", "moderate rain", "heavy intensity rain",
        "very heavy rain", "extreme rain", "light intensity shower rain", "shower rain", "heavy intensity shower rain", "ragged shower rain"],     # 09d, 09n, 10d, 10n

        "./assets/thunderstorm.png" : ["Thunderstorm", "thunderstorm with light rain", "thunderstorm with rain",
        "thunderstorm with heavy rain", "light thunderstorm", "thunderstorm", "thunderstorm", "heavy thunderstorm",
        "ragged thunderstorm", "thunderstorm with light drizzle", "thunderstorm with drizzle", "thunderstorm with heavy drizzle"]      # 11d, 11n
    }
    
    # Images name :   ( [ (Current ipadx, ipday Image frame)      (Week ipadx day frame, pady image frame)  ],
    #                   [ (current image width, height),           (week image width, height)               ],
    #                   [ Day Color header/current/week weather/extras, inner/current/week graph            ],
    #                   [ Night Color header/current/week weather/extras, inner/current/week graph          ]   )
    images_config = {   "./assets/sunny.png"        : ( [(10,  0), ( 9,  0)],  [(160, 160), ( 85,  80)], ["#F5B041", "#FFE082"], ["#55555D", "#929297"] ),
                        "./assets/clear_sky.png"    : ( [(10,  0), (10,  0)],  [(160, 120), ( 80,  80)], ["#03A9F4", "#81D4FA"], ["#21618C", "#2980B9"] ),
                        "./assets/cloudy.png"       : ( [(15,  5), ( 8,  5)],  [(130, 130), ( 90,  70)], ["#308DA5", "#87ceeb"], ["#308DA5", "#87ceeb"] ),
                        "./assets/foggy.png"        : ( [( 5, 10), (10,  5)],  [(170, 110), (110,  70)], ["#48C9B0", "#A3E4D7"], ["#E3915C", "#EDBB99"] ),
                        "./assets/snow.png"         : ( [(15,  5), (13,  0)],  [(160, 140), ( 90,  80)], ["#00BCD4", "#80DEEA"], ["#00BCD4", "#80DEEA"] ),
                        "./assets/windy.png"        : ( [( 0,  5), (10,  0)],  [(160, 145), (100,  80)], ["#34495E", "#AEB6BF"], ["#34495E", "#AEB6BF"] ),
                        "./assets/rainy.png"        : ( [(15,  0), ( 8,  0)],  [(160, 150), ( 80,  80)], ["#1976D2", "#64B5F6"], ["#1976D2", "#64B5F6"] ),
                        "./assets/thunderstorm.png" : ( [( 0,  0), ( 0,  1)],  [(160, 150), (100,  80)], ["#2980B9", "#7FB3D5"], ["#2980B9", "#7FB3D5"] )
                      }

    def __init__(self):
        super().__init__()
        self.title("Weather App")
        self.icon = "./assets/weather_app_logo.ico"
        self.wm_iconbitmap(self.icon)
        if self.view=="normal":
            self.width = 700
            self.height = 260
            self.geometry(f"{self.width}x{self.height}+{self.winfo_screenwidth()//3}+50")
        else:
            self.attributes("-topmost", False) 
            self.width = 1730
            self.height = 800
            self.geometry(f"{self.width}x{self.height}+{self.winfo_screenwidth()//20}+100")

        self.minsize(width=self.width, height=self.height)
        self.maxsize(width=self.width, height=self.height)
        self.resizable(False, False)

        self.Search_Frame()
        self.Search_Weather()


    def Search_Frame(self) -> None:
        """--------------------------| Search Frame |--------------------------
        Search frame includes, search entry, search, view, info, settings buttons
        Layout of search frame changes according to view button.
        """

        self.Sframe = tk.Frame(self, bg="cyan")
        #===============================| Normal |=====================================
        if self.view=="normal":
            #----------| Search Area Frame |----------

            self.sep_1st = tk.Label(self.Sframe, bg="cyan")
            self.sep_1st.grid(row=0, column=0, ipadx=110)

            #--------------------| Entry Field |--------------------
            self.city = tk.StringVar()
            self.city_entry = tk.Entry(self.Sframe, text=self.city, font=("Tahoma", 16, "bold"),
            bd=2, relief="flat", width=15, justify="center", bg="cyan")
            self.city_entry.grid(row=0, column=1, sticky="NE", ipady=3)

            #--------------------| Search Button |--------------------
            self.search_img = ImageTk.PhotoImage(Image.open("./assets/search.png").resize((30, 31)))
            self.search = tk.Button(self.Sframe, image=self.search_img, bg="cyan",
            relief="flat", overrelief="solid", command=self.Search_Weather)
            self.search.grid(row=0, column=2)

            self.sep_2nd = tk.Label(self.Sframe, bg="cyan")
            self.sep_2nd.grid(row=0, column=3, ipadx=50)

            #----------| ▼ Expand / ▲ Normal View Button |----------
            self.view_img = ImageTk.PhotoImage(Image.open("./assets/downarrowhead.png").resize((20, 20)))
            self.view_button = tk.Button(self.Sframe, image=self.view_img, relief="flat", overrelief="solid",
            bg="cyan", command=self.switch_layout)
            self.view_button.grid(row=0, column=4, ipadx=5, ipady=5)

            #--------------------| Info Button |--------------------
            self.info_img = ImageTk.PhotoImage(Image.open("./assets/info.png").resize((30, 30)))
            self.info_button = tk.Button(self.Sframe, image=self.info_img, relief="flat", overrelief="solid",
            bg="cyan", command=self.info)
            self.info_button.grid(row=0, column=5, padx=10, ipady=0)

            #--------------------| Settings Button |--------------------
            self.settings_img = ImageTk.PhotoImage(Image.open("./assets/settings.png").resize((25, 26)))
            self.settings_button = tk.Button(self.Sframe, image=self.settings_img, relief="flat",
            overrelief="solid", bg="cyan", command=self.settings)
            self.settings_button.grid(row=0, column=6, ipadx=2, ipady=2)
            self.Sframe.pack(anchor="n", side="top", fill="x", ipady=1)

        else:   #===============================| Expand |=====================================
            #----------| Search Area Frame |----------
            self.sep_1st = tk.Label(self.Sframe, bg="cyan")
            self.sep_1st.grid(row=0, column=0, ipadx=360)

            #--------------------| Entry Field |--------------------
            self.city = tk.StringVar()
            self.city_entry = tk.Entry(self.Sframe, text=self.city, font=("Tahoma", 18, "bold"),
            bd=2, relief="flat", width=20, justify="center", bg="cyan")
            self.city_entry.grid(row=0, column=1, sticky="NE", ipady=5)

            #--------------------| Search Button |--------------------
            self.search_img = ImageTk.PhotoImage(Image.open("./assets/search.png").resize((38, 38)))
            self.search = tk.Button(self.Sframe, image=self.search_img, relief="flat",
            overrelief="solid", command=self.Search_Weather)
            self.search.grid(row=0, column=2)

            self.sep_2nd = tk.Label(self.Sframe, bg="cyan")
            self.sep_2nd.grid(row=0, column=3, ipadx=180)

            #----------| ▼ Expand / ▲ Normal View Button |----------
            self.view_img = ImageTk.PhotoImage(Image.open("./assets/uparrowhead.png").resize((26, 26)))
            self.view_button = tk.Button(self.Sframe, image=self.view_img, bg="cyan",
            relief="flat", overrelief="solid", command=self.switch_layout)
            self.view_button.grid(row=0, column=4, ipadx=5, ipady=6)

            #--------------------| Info Button |--------------------
            self.info_img = ImageTk.PhotoImage(Image.open("./assets/info.png").resize((36, 36)))
            self.info_button = tk.Button(self.Sframe, image=self.info_img, bg="cyan",
            relief="flat", overrelief="solid", command=self.info)
            self.info_button.grid(row=0, column=5, ipady=1, padx=18)

            #--------------------| Settings Button |--------------------
            self.settings_img = ImageTk.PhotoImage(Image.open("./assets/settings.png").resize((30, 30)))
            self.settings_button = tk.Button(self.Sframe, image=self.settings_img, bg="cyan",
            relief="flat", overrelief="solid", command=self.settings)
            self.settings_button.grid(row=0, column=6, ipadx=2, ipady=4)

            #--------------------| Open Weather App Link |--------------------
            self.open_WImg = ImageTk.PhotoImage(Image.open("./assets/open_weather_logo.png").resize((100, 38)))
            self.open_weather = tk.Button(self.Sframe, image=self.open_WImg, bg="cyan",
            relief="flat", overrelief="solid", command=self.open_weather_link)
            self.open_weather.grid(row=0, column=7, ipadx=5, padx=10)
            self.Sframe.pack(anchor="n", side="top", fill="x", ipady=2)

        self.change_button_state()

        self.city_entry.insert(0, self.default_city)
        #--------------------| Bindings |--------------------
        self.city_entry.bind("<KeyRelease>", lambda e: self.city.set(self.city.get().upper()))
        self.city_entry.bind("<Return>", self.Search_Weather)
        self.search.bind("<Return>", self.Search_Weather)
        try:        # In Some systems it throws ERROR, maybe / not bind
            self.bind_all("</>", lambda e: (self.city_entry.focus(), self.city_entry.select_range(0, tk.END)))
        except tk.TclError:
            pass
        self.bind_all("<Control-s>", lambda e: self.search.invoke())
        self.bind_all("<Control-S>", lambda e: self.search.invoke())
        self.bind_all("<Control-i>", lambda e: self.settings_button.invoke())
        self.bind_all("<Control-I>", lambda e: self.settings_button.invoke())
        self.bind_all("<Control-v>", lambda e: self.view_button.invoke())
        self.bind_all("<Control-V>", lambda e: self.view_button.invoke())
        self.bind_all("<F9>", lambda e: self.info())

        self.temp = tk.Label(self, text="Loading...", font=("Tahoma", 18, "bold"), justify="center", bg="cyan")
        self.temp.pack(side="left", fill="both", ipadx=self.width//2)
        self.update()

    def Weather_Frames(self) -> None:
        """Make weather main frames with separators in the window and return them:
        1. Current Weather Frame
        -> Make current weather & graph frame 
            >> The main frame which includes current weather frame and graph frame

        2. Separater after current weather frame

        3. Week Weather Forecast Frame
        -> Make Week Weather Forecast & graph frame
            >> The main frame which includes week weather forecast frame and graph frame
        return:
            [f1, f2,...]"""

        #----------| Current Weather Frame |----------
        self.current_stats = tk.Frame(self, bg="cyan")
        self.current_stats.pack(anchor="nw", side="left", fill="both")
        
        # ----------| Side Separater Frame |----------
        self.side_sep = tk.Frame(self, bg="black")
        self.side_sep.pack(anchor="s", side="left", ipadx=1, ipady=357)

        #----------| Week Weather Forecast Frame |----------
        self.W_WForecast = tk.Frame(self, bg="cyan")
        self.W_WForecast.pack(anchor="nw", side="left", fill="both")

        self.update()


    def current_weather_details(self) -> dict[str, int | float | str]:
        """--------------------------| Current Weather Details |--------------------------
        It will make a Dictionary which holds, all values required in current temperature details.
        Image path, Image pady, Frame ipadx, Image size, bg color."""
        current_temp, current_feels, current_temp_name, current_temp_des, current_humid, current_visibility = self.current_weather()

        today_min, today_max = self.today_min_max_temp()
        current_time, current_date = self.current_time()

        _, _, current_city, _, current_country, current_region, current_time_zone, _ = self.location_details()

        current_sunrise, current_sunset = self.current_sun_time()
        current_moonrise, current_moonset = self.current_moon_time()

        for i in self.weather_images:
            if (current_temp_name in self.weather_images[i]) and (current_temp_des in self.weather_images[i]):
                current_image = i

                break
        raw_path = current_image.split("/")
        
        # If Time comes b/w sunrise and sunset
        if datetime.datetime.strptime(current_sunrise, "%I:%M %p")\
            <= datetime.datetime.strptime(current_time, "%I:%M %p") <= datetime.datetime.strptime(current_sunset, "%I:%M %p"):
            raw_path.insert(2, "day")       # add day image
            bg_img = self.images_config[current_image][2][0]
            fg_img = self.images_config[current_image][2][1]
        else:   # else add night image
            raw_path.insert(2, "night")
            bg_img = self.images_config[current_image][3][0]
            fg_img = self.images_config[current_image][3][1]

        current_exact_image = '/'.join(raw_path)

        current_details = { "Image" : current_exact_image, "bg color" : bg_img,
        "light color" : fg_img, "Image size" : self.images_config[current_image][1][0],
        "ipadx" : self.images_config[current_image][0][0][0], "ipady" : self.images_config[current_image][0][0][1],
        "Temp" : current_temp, "Feels" : current_feels, "Name" : current_temp_name,
        "Humidity" : current_humid, "Visibility" : current_visibility, "Min" : today_min, "Max" : today_max,
        "Time" : current_time, "Date" : current_date, "City" : current_city, "Country" : current_country,
        "Region" : current_region, "Time zone" : current_time_zone, "Sunrise" : current_sunrise,
        "Sunset" : current_sunset, "Moonrise" : current_moonrise, "Moonset" : current_moonset }
        return current_details

    def CW_Frame(self) -> None:
        """--------------------------| Current Weather Frame |--------------------------
        Make Current Weather Frame which includes:
        -> If Normal view   -> current weather image, weather, time, timezone, location, date, min, max, humidity
        -> If Detailed view -> all of Normal view"""
        self.temp.destroy()
        self.CW = self.current_weather_details()
        self.Sframe.configure(bg=self.CW["bg color"])
        self.sep_1st.configure(bg=self.CW["bg color"])
        self.sep_2nd.configure(bg=self.CW["bg color"])
        self.current_stats.configure(bg=self.CW["bg color"])
        self.W_WForecast.configure(bg=self.CW["bg color"])

        self.CWFrame = tk.Frame(self.current_stats, bg=self.CW["bg color"])

        #--------------------------| Current Weather main Frame |--------------------------
        self.CW_main = tk.Frame(self.CWFrame, bg=self.CW["bg color"], pady=5)

        #---------------| Current Weather Image Frame |---------------
        self.cw_img_frame = tk.LabelFrame(self.CW_main, text=self.CW["Name"], font=("Tahoma", 24),
        labelanchor="s", relief="flat", bg=self.CW["bg color"])

        #-----| Image |-----
        self.CImg = ImageTk.PhotoImage(Image.open(self.CW["Image"]).resize(self.CW["Image size"]))
        self.cw_img = tk.Label(master=self.cw_img_frame, image=self.CImg, bg=self.CW["bg color"])
        self.cw_img.pack()

        self.cw_img_frame.pack(anchor="nw", side="left", ipadx=self.CW["ipadx"], ipady=self.CW["ipady"])

        #---------------| Current Weather details Frame |---------------
        self.cwd_frame = tk.Frame(self.CW_main, bg=self.CW["bg color"])
        #-----| Temperature |-----
        if (self.CW["Temp"] < 0) and (len(str(self.CW["Temp"]))==5):
            self.ctemp = f' -{str(self.CW["Temp"])[1:]}°{self._unit.lower()}'

        elif len(str(self.CW["Temp"]))==4:
            self.ctemp = f' {str(self.CW["Temp"])}°{self._unit.lower()}'

        else:   self.ctemp = f' {str(self.CW["Temp"])}°{self._unit.lower()}'

        self.CTemp = tk.Label(self.cwd_frame, text=self.ctemp, font=("Tahoma", 60), bg=self.CW["bg color"])
        self.CTemp.grid(row=0, column=0, rowspan=3, sticky="se")

        #-----| Time |-----
        self.CTime = tk.Label(self.cwd_frame, text=f'{self.CW["Time"]:^11}', font=("Tahoma", 28), bg=self.CW["bg color"])
        self.CTime.grid(row=0, column=3, sticky="s", ipadx=5)
        
        #-----| Date |-----
        self.CDate = tk.Label(self.cwd_frame, text=f'{self.CW["Date"]:^16}', font=("Tahoma", 18), bg=self.CW["bg color"])
        self.CDate.grid(row=1, column=3, rowspan=2, sticky="n")

        #-----| Feel Like |-----
        self.Cfeels = tk.Label(self.cwd_frame, text=f"Feels like:{self.CW['Feels']:>9}°{self._unit.lower()}",
        font=("Tahoma", 18), bg=self.CW["bg color"])
        self.Cfeels.grid(row=3, column=0, columnspan=2, sticky="nswe")

        #-----| Minimum |-----
        self.CMin = tk.Label(self.cwd_frame, text=f"Min:\t{self.CW['Min']:>8}°{self._unit.lower()}",
        font=("Tahoma", 18), bg=self.CW["bg color"])
        self.CMin.grid(row=4, column=0, columnspan=2, sticky="nswe")

        #-----| Maximum |-----
        self.CMax = tk.Label(self.cwd_frame, text=f"Max:\t{self.CW['Max']:>8}°{self._unit.lower()}",
        font=("Tahoma", 18), bg=self.CW["bg color"])
        self.CMax.grid(row=5, column=0, columnspan=2, sticky="nswe")

        #-----| Time Zone |-----
        self.CTZone= tk.Label(self.cwd_frame, text=f"GMT {self.CW['Time zone'][:-2] + ':' + self.CW['Time zone'][-2:]}",
        font=("Tahoma", 18), bg=self.CW["bg color"])
            
        #-----| City |-----
        self.CCity = tk.Label(self.cwd_frame, text=f'{self.CW["City"]:^20}', font=("Tahoma", 18), bg=self.CW["bg color"])

        #-----| Country, Continent |-----
        if (" " in self.CW["Country"]) or (len(self.CW["Country"]) >= 10):
            self.con = self.CW["Country"]
        else:
            self.con = self.CW["Country"] + ", " + self.CW["Region"]

        self.CCon = tk.Label(self.cwd_frame, text=f"{self.con:^20}", font=("Tahoma", 18), bg=self.CW["bg color"])

        if self.view=="expand":
            self.CTZone.grid(row=3, column=3, sticky="nswe")
            self.CCity.grid(row=4, column=3, sticky="nswe")
            self.CCon.grid(row=5, column=3, sticky="nswe")

        else:
            self.CCity.grid(row=3, column=3, sticky="nswe")
            self.CCon.grid(row=4, column=3, sticky="nswe")

        self.cwd_frame.pack(anchor="nw", side="left")
        self.CW_main.pack(side="top", ipadx=10)
        self.cw_sep = tk.Frame(self.CWFrame, bg="black")
        self.cw_sep.pack(side="top", fill="x", pady=5)
        
        #--------------------------| Current Weather more Frame |--------------------------
        self.CW_more = tk.Frame(self.CWFrame, bg=self.CW["bg color"])

        #--------------------| Sunrise |--------------------
        self.CSR = tk.Label(self.CW_more, text="  Sunrise", font=("Tahoma", 16), bg=self.CW["bg color"], justify="left")
        self.CSR.grid(row=0, column=0, sticky="ne")
        self.CSR_img = ImageTk.PhotoImage(Image.open("./assets/sunrise.png").resize((30, 30)))
        self.CSR_logo = tk.Label(self.CW_more, image=self.CSR_img, bg=self.CW["bg color"])
        self.CSR_logo.grid(row=0, column=1, sticky="nw")
        self.CSR_time = tk.Label(self.CW_more, text=f'{self.CW["Sunrise"].lower():>12}', font=("Tahoma", 16),
        bg=self.CW["bg color"], justify="left")
        self.CSR_time.grid(row=0, column=2, sticky="nw")

        #--------------------| Sunset |--------------------
        self.CSS = tk.Label(self.CW_more, text="\tSunset", font=("Tahoma", 16), bg=self.CW["bg color"])
        self.CSS.grid(row=0, column=3, sticky="ne")
        self.CSS_img = ImageTk.PhotoImage(Image.open("./assets/sunset.png").resize((35, 25)))
        self.CSS_logo = tk.Label(self.CW_more, image=self.CSS_img, bg=self.CW["bg color"])
        self.CSS_logo.grid(row=0, column=4, sticky="s")
        self.CSS_time = tk.Label(self.CW_more, text=f'{self.CW["Sunset"].lower():>12}', font=("Tahoma", 16),
        bg=self.CW["bg color"], justify="left")
        self.CSS_time.grid(row=0, column=5, sticky="nw")

        #--------------------| Moonrise |--------------------
        self.CMR = tk.Label(self.CW_more, text="Moonrise", font=("Tahoma", 16), bg=self.CW["bg color"], justify="left")
        self.CMR.grid(row=1, column=0, sticky="ne")
        self.CMR_img = ImageTk.PhotoImage(Image.open("./assets/moonrise.png").resize((30, 30)))
        self.CMR_logo = tk.Label(self.CW_more, image=self.CMR_img, bg=self.CW["bg color"])
        self.CMR_logo.grid(row=1, column=1, sticky="nw")
        self.CMR_time = tk.Label(self.CW_more, text=f'{self.CW["Moonrise"].lower():>12}', font=("Tahoma", 16),
        bg=self.CW["bg color"], justify="left")
        self.CMR_time.grid(row=1, column=2, sticky="nw")

        #--------------------| Moonset |--------------------
        self.CMS = tk.Label(self.CW_more, text="Moonset", font=("Tahoma", 16), bg=self.CW["bg color"], justify="left")
        self.CMS.grid(row=1, column=3, sticky="ne")
        self.CMS_img = ImageTk.PhotoImage(Image.open("./assets/moonset.png").resize((35, 25)))
        self.CMS_logo = tk.Label(self.CW_more, image=self.CMS_img, bg=self.CW["bg color"])
        self.CMS_logo.grid(row=1, column=4, sticky="sw")
        self.CMS_time = tk.Label(self.CW_more, text=f'{self.CW["Moonset"].lower():>12}', font=("Tahoma", 16),
        bg=self.CW["bg color"], justify="left")
        self.CMS_time.grid(row=1, column=5, sticky="nw")

        #--------------------| Humidity |--------------------
        self.CHumid = tk.Label(self.CW_more, text="Humidity", font=("Tahoma", 16), bg=self.CW["bg color"], justify="left")
        self.CHumid.grid(row=2, column=0, sticky="ne")
        self.CHumid_img = ImageTk.PhotoImage(Image.open("./assets/humidity.png").resize((35, 25)))
        self.CHumidity_logo = tk.Label(self.CW_more, image=self.CHumid_img, bg=self.CW["bg color"])
        self.CHumidity_logo.grid(row=2, column=1, sticky="nw")
        self.CHumid_mark = tk.Label(self.CW_more, text=f'{self.CW["Humidity"]:>6}%', font=("Tahoma", 16),
        bg=self.CW["bg color"], justify="left")
        self.CHumid_mark.grid(row=2, column=2, sticky="nw")

        #--------------------| Weather Type Detail |--------------------
        self.CVisible = tk.Label(self.CW_more, text="Visibility", font=("Tahoma", 16), bg=self.CW["bg color"], justify="left")
        self.CVisible.grid(row=2, column=3, sticky="ne")
        self.CVisible_img = ImageTk.PhotoImage(Image.open("./assets/visibility.png").resize((35, 25)))
        self.CVisible_logo = tk.Label(self.CW_more, image=self.CVisible_img, bg=self.CW["bg color"])
        self.CVisible_logo.grid(row=2, column=4, sticky="sw")
        self.CVisible_mark = tk.Label(self.CW_more, text=f'{self.CW["Visibility"]/1000:>7} km',
        font=("Tahoma", 16), bg=self.CW["bg color"], justify="left")
        self.CVisible_mark.grid(row=2, column=5, sticky="nw")

        self.CW_more.pack(anchor="s", side="bottom", pady=8)
        self.CWFrame.grid(row=0, column=0, sticky="nswe")
        self.update()


    def CW_show_temp(self, event) -> None:
        """---------------------| Shows the Current selected point temp in graph |---------------------
        It will call upon when mouse button is clicked on temperature line graph"""

        Ccoord = []
        Ccoord.append((event.xdata, event.ydata))
        Cx = event.xdata
        Cy = event.ydata
        
        # Setting the temperature based on axis
        self.cw_annot.xy = (Cx, Cy)
        try:
            self.cw_annot.set_text(f"{self.temps[int(Cx)]}°{self._unit.lower()}")
            self.cw_annot.set_visible(True)
            self.cw_canvas.draw()
        except TypeError:       # If mouse axis out of plotted area
            pass

    
    def CW_graph(self) -> None:
        """--------------------------| Current Day Temp Graph |--------------------------
        Display the graph of current day, well-labelled"""

        #---------------------| Figure area for Graph |---------------------
        self.cw_fig = Figure(figsize=(7, 4.15), dpi=100, facecolor=self.CW["light color"], tight_layout={'h_pad' : 3, 'w_pad' : 0})

        #---------------------| Data which display in Graph |---------------------
        current_day_temp = self.current_day_temps()
        self.hours = [h for h in current_day_temp.keys()]
        self.temps = [t for t in current_day_temp.values()]

        #---------------------| Plotting Line Graph |---------------------
        self.cw_graph = self.cw_fig.add_subplot(111)
        self.cw_graph.plot(self.hours, self.temps)
        self.cw_graph.plot(self.hours, self.temps, color="black", linestyle="-", linewidth=3, marker="o", markersize=9, markerfacecolor=self.CW["bg color"])
        self.cw_graph.set_title(label="Temperature from now to next 24 hours", fontdict={"fontfamily" : "Tahoma", "fontsize" : 16})
        self.cw_graph.set_facecolor(self.CW["light color"])
        self.cw_graph.spines["right"].set_visible(False)
        self.cw_graph.spines["top"].set_visible(False)
        self.cw_graph.spines["left"].set_visible(False)

        #---------------------| Labels and ticks on X-axis |---------------------
        self.x_ticks = ['\n'.join(i.split('\n')[1].split(' ')).lower() for i in self.hours]
        self.cw_graph.set_xticks(self.hours)
        self.cw_graph.set_xticklabels(labels=self.x_ticks, fontfamily="Tahoma", fontsize=11)
        self.cw_graph.set_xlabel(xlabel="Time", fontfamily="Tahoma", fontsize=14)

        #---------------------| Label and no ticks on Y-axis |---------------------
        self.cw_graph.set_yticks([])
        
        #---------------------| Cursor which spanes the axis when mouse moves over |---------------------
        Cursor(ax=self.cw_graph, horizOn=False, vertOn=False, useblit=True, color = "r", linewidth = 1)

        #---------------------| Annotated box on which clicked area temp. display |---------------------
        self.cw_annot = self.cw_graph.annotate(text="", xy=(self.x_ticks[0], 0), xytext=(10, 20),
            textcoords="offset points", arrowprops={"arrowstyle" : "fancy"}, annotation_clip=True,
            bbox={"boxstyle" : "round, pad=0.5", "fc" : self.CW["light color"], "ec" : "black", "lw" : 2}, size=10 )
        self.cw_annot.set_visible(True)

        #---------------------| Canvas to place the Graph Figure |---------------------
        self.cw_canvas = FigureCanvasTkAgg(self.cw_fig, master=self.current_stats)
        self.cw_canvas.mpl_connect('button_press_event', self.CW_show_temp)
        self.cw_canvas.draw()
        self.cw_canvas.get_tk_widget().grid(row=2, column=0, sticky="nswe")

    
    def week_forecast_details(self) -> list[dict[str, int | float | str]]:
        """--------------------------| Week Weather Forecast Details |--------------------------
        It will make a list of dictionaries which holds, all values in seven_days_forecast() return dict
        as well as some extra things:
        Image path, Image pady, Frame ipadx, Image size, bg color"""

        week_forecast = self.Seven_days_forecast()
        raw_Wdetails = []
        for i, day in enumerate(week_forecast):

            #-----| Getting image according to weather |-----
            for image, group in self.weather_images.items():
                if (day["Name"] and day["Description"] in group):
                    raw_path = image.split('/')
                    img_path = "./" + raw_path[1] + "/day/" + raw_path[-1]
                    break

            Ipady = self.images_config[image][0][1][1]
            Fipadx = self.images_config[image][0][1][0]
            size = self.images_config[image][1][1]
            color = self.CW["bg color"]

            # storing all required details in a dict format
            details = {**day, "Image" : img_path, "Image pady" : Ipady, "Frame ipadx" : Fipadx, "Image size" : size, "bg color" : color}
            if not i:
                details["Date"] = "Tomorrow"
            
            raw_Wdetails.append(details)

        return raw_Wdetails


    def WF_Frame(self) -> None:
        """--------------------------| Week Weather Forecast Frame |--------------------------
        Make Week Forecast Frame which includes:
        -> A main frame which includes 7 frames (each day of week)
        -> Each Subframe will display the Date, Temperature, Day, night temp"""

        #----------| Week Weather Forecast Frame |----------
        self.WF_details = self.week_forecast_details()
        self.week_Forecast = tk.Frame(self.W_WForecast, bg=self.WF_details[0]["bg color"], pady=27)

        #============================| Tomorrow Frame |============================
        self.Tomorrow = tk.Frame(self.week_Forecast, bg=self.WF_details[0]["bg color"])
        #----------| Tomorrow Date |----------
        self.TDate = tk.Label(self.Tomorrow, text=self.WF_details[0]["Date"], font=("Tahoma", 18), justify="center", bg=self.WF_details[0]["bg color"])
        self.TDate.pack(side="top", fill="x")

        #----------| Tomorrow Weather |----------
        self.TWeather = tk.LabelFrame(self.Tomorrow, text=f'{int(self.WF_details[0]["Temp"]):>3}°{self._unit.lower()}\n{self.WF_details[0]["Name"]}',
        font=("Tahoma", 18), labelanchor="s", relief="flat", bg=self.WF_details[0]["bg color"])
        self.Timg = ImageTk.PhotoImage(Image.open(self.WF_details[0]["Image"]).resize(self.WF_details[0]["Image size"]))
        self.TW_image = tk.Label(self.TWeather, image=self.Timg, bg=self.WF_details[0]["bg color"])
        self.TW_image.pack(side="top", fill="both", pady=self.WF_details[0]["Image pady"])
        self.TWeather.pack(side="top", fill="x", pady=20)

        #----------| Tomorrow Day Temp|----------
        self.TDay = tk.Label(self.Tomorrow, text=f" {'Day:':<9}{int(self.WF_details[0]['Day:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[0]["bg color"])
        self.TDay.pack(side="top", fill="x")

        #----------| Tomorrow Night Temp |----------
        self.TNight = tk.Label(self.Tomorrow, text=f" {'Night:':<9}{int(self.WF_details[0]['Night:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[0]["bg color"])
        self.TNight.pack(side="top", fill="x")
        self.Tomorrow.grid(row=0, column=0, sticky="nswe", ipadx=self.WF_details[0]["Frame ipadx"], ipady=5)

        #============================| Day2 Frame |============================
        self.Day2 = tk.Frame(self.week_Forecast, bg=self.WF_details[1]["bg color"])
        #----------| Day2 Date |----------
        self.D2Date = tk.Label(self.Day2, text=self.WF_details[1]["Date"], font=("Tahoma", 18), justify="center", bg=self.WF_details[1]["bg color"])
        self.D2Date.pack(side="top", fill="x")

        #----------| Day2 Weather |----------
        self.D2weather = tk.LabelFrame(self.Day2, text=f'{int(self.WF_details[1]["Temp"]):>3}°{self._unit.lower()}\n{self.WF_details[1]["Name"]}',
        font=("Tahoma", 18), labelanchor="s", relief="flat", bg=self.WF_details[1]["bg color"])
        self.D2img = ImageTk.PhotoImage(Image.open(self.WF_details[1]["Image"]).resize(self.WF_details[1]["Image size"]))
        self.D2w_image = tk.Label(self.D2weather, image=self.D2img, bg=self.WF_details[1]["bg color"])
        self.D2w_image.pack(side="top", fill="both", pady=self.WF_details[1]["Image pady"])
        self.D2weather.pack(side="top", fill="x", pady=20)

        #----------| Day2 Day Temp|----------
        self.D2day = tk.Label(self.Day2, text=f" {'Day:':<9}{int(self.WF_details[1]['Day:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[1]["bg color"])
        self.D2day.pack(side="top", fill="x")

        #----------| Day2 Night Temp |----------
        self.D2night = tk.Label(self.Day2, text=f" {'Night:':<9}{int(self.WF_details[1]['Night:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[1]["bg color"])
        self.D2night.pack(side="top", fill="x")
        self.Day2.grid(row=0, column=1, sticky="nswe", ipadx=self.WF_details[1]["Frame ipadx"])

        #============================| Day3 Frame |============================
        self.Day3 = tk.Frame(self.week_Forecast, bg=self.WF_details[2]["bg color"])
        #----------| Day3 Date |----------
        self.D3Date = tk.Label(self.Day3, text=self.WF_details[2]["Date"], font=("Tahoma", 18), justify="center", bg=self.WF_details[2]["bg color"])
        self.D3Date.pack(side="top", fill="x")

        #----------| Day3 Weather |----------
        self.D3weather = tk.LabelFrame(self.Day3, text=f'{int(self.WF_details[2]["Temp"]):>3}°{self._unit.lower()}\n{self.WF_details[2]["Name"]}',
        font=("Tahoma", 18), labelanchor="s", relief="flat", bg=self.WF_details[2]["bg color"])
        self.D3img = ImageTk.PhotoImage(Image.open(self.WF_details[2]["Image"]).resize(self.WF_details[2]["Image size"]))
        self.D3w_image = tk.Label(self.D3weather, image=self.D3img, bg=self.WF_details[2]["bg color"])
        self.D3w_image.pack(side="top", fill="both", pady=self.WF_details[2]["Image pady"])
        self.D3weather.pack(side="top", fill="x", pady=20)

        #----------| Day3 Day Temp|----------
        self.D3day = tk.Label(self.Day3, text=f" {'Day:':<9}{int(self.WF_details[2]['Day:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[2]["bg color"])
        self.D3day.pack(side="top", fill="x")

        #----------| Day3 Night Temp |----------
        self.D3night = tk.Label(self.Day3, text=f" {'Night:':<9}{int(self.WF_details[2]['Night:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[2]["bg color"])
        self.D3night.pack(side="top", fill="x")
        self.Day3.grid(row=0, column=2, sticky="nswe", ipadx=self.WF_details[2]["Frame ipadx"])

        #============================| Day4 Frame |============================
        self.Day4 = tk.Frame(self.week_Forecast, bg=self.WF_details[3]["bg color"])
        #----------| Day4 Date |----------
        self.D4Date = tk.Label(self.Day4, text=self.WF_details[3]["Date"], font=("Tahoma", 18), justify="center", bg=self.WF_details[3]["bg color"])
        self.D4Date.pack(side="top", fill="x")

        #----------| Day4 Weather |----------
        self.D4weather = tk.LabelFrame(self.Day4, text=f'{int(self.WF_details[3]["Temp"]):>3}°{self._unit.lower()}\n{self.WF_details[3]["Name"]}',
        font=("Tahoma", 18), labelanchor="s", relief="flat", bg=self.WF_details[3]["bg color"])
        self.D4img = ImageTk.PhotoImage(Image.open(self.WF_details[3]["Image"]).resize(self.WF_details[3]["Image size"]))
        self.D4w_image = tk.Label(self.D4weather, image=self.D4img, bg=self.WF_details[3]["bg color"])
        self.D4w_image.pack(side="top", fill="both", pady=self.WF_details[3]["Image pady"])
        self.D4weather.pack(side="top", fill="x", pady=20)

        #----------| Day4 Day Temp|----------
        self.D4day = tk.Label(self.Day4, text=f" {'Day:':<9}{int(self.WF_details[3]['Day:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[3]["bg color"])
        self.D4day.pack(side="top", fill="x")

        #----------| Day4 Night Temp |----------
        self.D4night = tk.Label(self.Day4, text=f" {'Night:':<9}{int(self.WF_details[3]['Night:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[3]["bg color"])
        self.D4night.pack(side="top", fill="x")
        self.Day4.grid(row=0, column=3, sticky="nswe", ipadx=self.WF_details[3]["Frame ipadx"])

        #============================| Day5 Frame |============================
        self.Day5 = tk.Frame(self.week_Forecast, bg=self.WF_details[4]["bg color"])
        #----------| Day5 Date |----------
        self.D5Date = tk.Label(self.Day5, text=self.WF_details[4]["Date"], font=("Tahoma", 18), justify="center", bg=self.WF_details[4]["bg color"])
        self.D5Date.pack(side="top", fill="x")

        #----------| Day5 Weather |----------
        self.D5weather = tk.LabelFrame(self.Day5, text=f'{int(self.WF_details[4]["Temp"]):>3}°{self._unit.lower()}\n{self.WF_details[4]["Name"]}',
        font=("Tahoma", 18), labelanchor="s", relief="flat", bg=self.WF_details[4]["bg color"])
        self.D5img = ImageTk.PhotoImage(Image.open(self.WF_details[4]["Image"]).resize(self.WF_details[4]["Image size"]))
        self.D5w_image = tk.Label(self.D5weather, image=self.D5img, bg=self.WF_details[4]["bg color"])
        self.D5w_image.pack(side="top", fill="both", pady=self.WF_details[4]["Image pady"])
        self.D5weather.pack(side="top", fill="x", pady=20)

        #----------| Day5 Day Temp|----------
        self.D5day = tk.Label(self.Day5, text=f" {'Day:':<9}{int(self.WF_details[4]['Day:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[4]["bg color"])
        self.D5day.pack(side="top", fill="x")

        #----------| Day5 Night Temp |----------
        self.D5night = tk.Label(self.Day5, text=f" {'Night:':<9}{int(self.WF_details[4]['Night:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[4]["bg color"])
        self.D5night.pack(side="top", fill="x")
        self.Day5.grid(row=0, column=4, sticky="nswe", ipadx=self.WF_details[4]["Frame ipadx"])

        #============================| Day6 Frame |============================
        self.Day6 = tk.Frame(self.week_Forecast, bg=self.WF_details[5]["bg color"])
        #----------| Day6 Date |----------
        self.D6Date = tk.Label(self.Day6, text=self.WF_details[5]["Date"], font=("Tahoma", 18), justify="center", bg=self.WF_details[5]["bg color"])
        self.D6Date.pack(side="top", fill="x")

        #----------| Day6 Weather |----------
        self.D6weather = tk.LabelFrame(self.Day6, text=f'{int(self.WF_details[5]["Temp"]):>3}°{self._unit.lower()}\n{self.WF_details[5]["Name"]}',
        font=("Tahoma", 18), labelanchor="s", relief="flat", bg=self.WF_details[5]["bg color"])
        self.D6img = ImageTk.PhotoImage(Image.open(self.WF_details[5]["Image"]).resize(self.WF_details[5]["Image size"]))
        self.D6w_image = tk.Label(self.D6weather, image=self.D6img, bg=self.WF_details[5]["bg color"])
        self.D6w_image.pack(side="top", fill="both", pady=self.WF_details[5]["Image pady"])
        self.D6weather.pack(side="top", fill="x", pady=20)

        #----------| Day6 Day Temp|----------
        self.D6day = tk.Label(self.Day6, text=f" {'Day:':<9}{int(self.WF_details[5]['Day:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14),justify="center", bg=self.WF_details[5]["bg color"])
        self.D6day.pack(side="top", fill="x")

        #----------| Day6 Night Temp |----------
        self.D6night = tk.Label(self.Day6, text=f" {'Night:':<9}{int(self.WF_details[5]['Night:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[5]["bg color"])
        self.D6night.pack(side="top", fill="x")
        self.Day6.grid(row=0, column=5, sticky="nswe", ipadx=self.WF_details[5]["Frame ipadx"])

        #============================| Day7 Frame |============================
        self.Day7 = tk.Frame(self.week_Forecast, bg=self.WF_details[6]["bg color"])
        #----------| Day7 Date |----------
        self.D7Date = tk.Label(self.Day7, text=self.WF_details[6]["Date"], font=("Tahoma", 18), justify="center", bg=self.WF_details[6]["bg color"])
        self.D7Date.pack(side="top", fill="x")

        #----------| Day7 Weather |----------
        self.D7weather = tk.LabelFrame(self.Day7, text=f'{int(self.WF_details[6]["Temp"]):>3}°{self._unit.lower()}\n{self.WF_details[6]["Name"]}',
        font=("Tahoma", 18), labelanchor="s", relief="flat", bg=self.WF_details[6]["bg color"])
        self.D7img = ImageTk.PhotoImage(Image.open(self.WF_details[6]["Image"]).resize(self.WF_details[6]["Image size"]))
        self.D7w_image = tk.Label(self.D7weather, image=self.D7img, bg=self.WF_details[6]["bg color"])
        self.D7w_image.pack(side="top", fill="both", pady=self.WF_details[6]["Image pady"])
        self.D7weather.pack(side="top", fill="x", pady=20)

        #----------| Day7 Day Temp|----------
        self.D7day = tk.Label(self.Day7, text=f" {'Day:':<9}{int(self.WF_details[6]['Day:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[6]["bg color"])
        self.D7day.pack(side="top", fill="x")

        #----------| Day7 Night Temp |----------
        self.D7night = tk.Label(self.Day7, text=f" {'Night:':<9}{int(self.WF_details[6]['Night:']):>3}°{self._unit.lower()}",
        font=("Tahoma", 14), justify="center", bg=self.WF_details[6]["bg color"])
        self.D7night.pack(side="top", fill="x")
        self.Day7.grid(row=0, column=6, sticky="nswe", ipadx=self.WF_details[6]["Frame ipadx"])

        #----------| Extra pad space to cover empty area |----------
        self.extra = tk.Frame(self.week_Forecast)
        self.extra.grid(row=0, column=7, padx=5)
        self.week_Forecast.grid(row=0, column=0, sticky="nswe", ipadx=7)
        self.update()


    def WF_show_temp(self, event) -> None:
        """---------------------| Shows the week selected point temp in graph |---------------------
        It will call upon when mouse button is clicked on temperature line graph"""

        Wcoord = []
        Wcoord.append((event.xdata, event.ydata))
        Wx = event.xdata
        Wy = event.ydata
        
        # Setting the temperature based on axis
        self.week_annot.xy = (Wx, Wy)
        try:
            self.week_annot.set_text(f"{self.Temps[int(Wx)]}°{self._unit.lower()}")
            self.week_annot.set_visible(True)
            self.week_canvas.draw()
        except TypeError:   # if mouse axis is out of ploted area
            pass

    
    def WF_graph(self) -> None:
        """--------------------------| Week Weather Forecast Graph |--------------------------
        Display the graph of current day, well-labelled"""

        #---------------------| Figure area for Graph |---------------------
        #             (width, height) (dots per inch, use less dpi)  (fg color)    (layout height, width)
        self.week_fig = Figure(figsize=(10.25, 4.15), dpi=100, facecolor=self.CW["light color"], tight_layout={'h_pad' : 3})
        #---------------------| Data which display in Graph |---------------------
        seven_days = self.Seven_days_forecast()
        self.Dates = [ day["Date"] for day in seven_days]
        self.Temps = [ day["Temp"] for day in seven_days]

        #---------------------| Plotting Line Graph |---------------------
        self.week_graph = self.week_fig.add_subplot(111)
        self.week_graph.plot(self.Dates, self.Temps, color="black", linestyle="-", linewidth=3, marker="o", markersize=9, markerfacecolor=self.CW["bg color"])
        self.week_graph.set_title(label="Temperature of next 7 days", fontdict={"fontfamily" : "Tahoma", "fontsize": 16}, color="black")
        self.week_graph.set_facecolor(self.CW["light color"])
        self.week_graph.spines["right"].set_visible(False)
        self.week_graph.spines["top"].set_visible(False)
        self.week_graph.spines["left"].set_visible(False)
        self.week_graph.spines["bottom"].set_color("black")

        #---------------------| Labels and ticks on X-axis |---------------------
        self.X_ticks = [date for date in self.Dates]
        self.week_graph.set_xticks(self.Dates)
        self.week_graph.set_xticklabels(labels=self.X_ticks, fontfamily="Tahoma", fontsize=12, color="black")
        self.week_graph.set_xlabel(xlabel="Date", color="black", fontfamily="Tahoma", fontsize=14)

        #---------------------| Labels and ticks on Y-axis |---------------------
        self.week_graph.set_yticks([])

        #---------------------| Cursor which spanes the axis when mouse moves over |---------------------
        Cursor(ax=self.week_graph, horizOn=False, vertOn=False, useblit=True,
                        color = "r", linewidth = 1)

        #---------------------| Annotated box on which clicked area temp. display |---------------------
        self.week_annot = self.week_graph.annotate(text="", xy=(self.X_ticks[0], 0), xytext=(10, 20),
            textcoords="offset points", arrowprops={"arrowstyle" : "fancy"}, annotation_clip=True,
            bbox={"boxstyle" : "round, pad=0.5", "fc" : self.CW["light color"], "ec" : "black", "lw" : 2}, size=10)
        self.week_annot.set_visible(True)

        #---------------------| Canvas to place the Graph Figure |---------------------
        self.week_canvas = FigureCanvasTkAgg(figure=self.week_fig, master=self.W_WForecast)
        self.week_canvas.mpl_connect('button_press_event', self.WF_show_temp)
        self.week_canvas.draw()
        self.week_canvas.get_tk_widget().grid(row=2, column=0, sticky="nw")


    def info(self) -> None:
        """#--------------------------------------| Info Window |--------------------------------------
        Display Info window, in which all information of Weather App will show"""

        try:    # If info is already open
            self.info_win.focus()
            return
        except (AttributeError, tk.TclError):
            pass
        #--------------------------------------| Info Window |--------------------------------------
        self.info_win = tk.Toplevel(self, bg=self.CW["bg color"])
        self.info_win.focus()
        self.info_win.title("Weather App - Info")
        self.info_win.wm_iconbitmap(self.icon)
        self.info_win.geometry("500x620")
        self.info_win.minsize(width=500, height=620)
        self.info_win.maxsize(width=500, height=620)
        self.info_win.resizable(False, False)
        #--------------------------------------| Info Label |--------------------------------------
        self.info_label = tk.Label(self.info_win, text="Info", font=("Tahoma", 18, "bold"), bg=self.CW["bg color"], justify="center")
        self.info_label.pack(side="top", fill="x", pady=10)
        self.info_sep1 = tk.Frame(self.info_win, bg="black")
        self.info_sep1.pack(side="top", fill="x", padx=10, pady=5)

        #--------------------------------------| Developer Label |--------------------------------------
        self.dev_detail = tk.Label(self.info_win, text="This Application is developed by Parampreet Singh.", font=("Tahoma", 12), bg=self.CW["bg color"], padx=20)
        self.dev_detail.pack(side="top", anchor="nw")
        self.dev_github = tk.Button(self.info_win, text="https://github.com/Param302", font=("Tahoma", 10), bg=self.CW["bg color"], fg="blue",activebackground=self.CW["bg color"], relief="flat", overrelief="flat", padx=20, command=self.github_link)
        self.dev_github.pack(side="top", anchor="nw")
        self.info_sep2 = tk.Frame(self.info_win, bg="black")
        self.info_sep2.pack(side="top", fill="x", padx=10, pady=5)

        #--------------------------------------| WA details |--------------------------------------
        self.WA_details = tk.LabelFrame(self.info_win, text="Data Details", font=("Tahoma", 14, "bold"),
        bg=self.CW["bg color"], padx=10, pady=5, relief="flat")
        #--------------------------| Starting |--------------------------
        self.wa_start = tk.Label(self.WA_details, text="All weather data is being fetched from OpenWeathermap APIs:",
        font=("Tahoma", 12), bg=self.CW["bg color"], justify="left", padx=10)       
        self.wa_start.grid(row=0, column=0, columnspan=2, sticky="w")

        #--------------------------| Current Weather Data API button |--------------------------
        self.current_api_button = tk.Button(self.WA_details, text="• Current Weather Data API",
        font=("Tahoma", 12, "underline"), bg=self.CW["bg color"], activebackground=self.CW["bg color"],
        fg="blue", justify="left", relief="flat", overrelief="flat", padx=10, command=self.current_api_link)
        self.current_api_button.grid(row=1, column=0, sticky="w")

        #--------------------------| One Call API button |--------------------------
        self.one_call_api_button = tk.Button(self.WA_details, text="• One Call API",
        font=("Tahoma", 12, "underline"), bg=self.CW["bg color"], activebackground=self.CW["bg color"],
        fg="blue", justify="left", relief="flat", overrelief="flat", padx=10, command=self.one_call_api_link)
        self.one_call_api_button.grid(row=2, column=0, sticky="w")

        #--------------------------| Open Weather map image button |--------------------------
        self.OW_img = ImageTk.PhotoImage(Image.open("./assets/open_weather_logo.png").resize((100, 40)))
        self.OW_logo = tk.Button(self.WA_details, image=self.OW_img, bg=self.CW["bg color"],
        activebackground=self.CW["bg color"], relief="flat", overrelief="solid", padx=10, command=self.open_weather_link)
        self.OW_logo.grid(row=1, column=1, rowspan=2, sticky="w")
        self.OW_logo.bind("<Enter>", lambda e: self.OW_logo.configure(bg=self.CW["light color"]))
        self.OW_logo.bind("<Leave>", lambda e: self.OW_logo.configure(bg=self.CW["bg color"]))

        #--------------------------| Extra Details about App |--------------------------
        self.wa_extra = tk.Label(self.WA_details, text="It display Current Weather details\
and 7-day Weather Forecast with Next 24 hour Temperature Graph of 3 hour interval and Weekly Temperature Graph on daily interval.\
\n\nDay Temperature of 7-day Weather Forecast is being considered for temperature as well as graph.\
\n\nPlease try to search weather after interval of 15 seconds to keep application stable.",
        font=("Tahoma", 12), bg=self.CW["bg color"], justify="left", padx=10, wraplength=450)
        self.wa_extra.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)

        self.WA_details.pack(side="top", fill="x", pady=10)
        self.info_sep3 = tk.Frame(self.info_win, bg="black")
        self.info_sep3.pack(side="top", fill="x", padx=10)

        #--------------------------------------| Shortcut Keys |--------------------------------------
        self.Shortcut_keys = tk.LabelFrame(self.info_win, text=" Shortcut Keys", font=("Tahoma", 14, "bold"),
        bg=self.CW["bg color"], padx=30, pady=10, relief="flat")
        #----------| Info Label |----------
        self.info_label = tk.Label(self.Shortcut_keys, text="Info", font=("Tahoma", 12),
        bg=self.CW["bg color"], justify="left", padx=10)
        self.info_label.grid(row=0, column=0, sticky="e", pady=5)

        #----------| Info key |----------
        self.info_key = tk.Label(self.Shortcut_keys, text="F9", font=("Tahoma", 12),
        bg=self.CW["light color"], justify="left", padx=10)
        self.info_key.grid(row=0, column=1, sticky="nswe", pady=5)
        self.info_side_sep = tk.Frame(self.Shortcut_keys, bg=self.CW["bg color"])
        self.info_side_sep.grid(row=0, column=2, rowspan=2, ipadx=20)

        #----------| Layout Label |----------
        self.layout_label = tk.Label(self.Shortcut_keys, text="Layout", font=("Tahoma", 12),
        bg=self.CW["bg color"], justify="left", padx=10)
        self.layout_label.grid(row=0, column=3, sticky="e", pady=5)

        #----------| Layout Key |----------
        self.layout_key = tk.Label(self.Shortcut_keys, text="Control + v", font=("Tahoma", 12),
        bg=self.CW["light color"], justify="left", padx=10)
        self.layout_key.grid(row=0, column=4, sticky="nswe", pady=5)

        #----------| Search Label |----------
        self.search_label = tk.Label(self.Shortcut_keys, text="Search", font=("Tahoma", 12),
        bg=self.CW["bg color"], justify="left", padx=10)
        self.search_label.grid(row=1, column=0, sticky="e", pady=5)

        #----------| Search Key |----------
        self.search_key = tk.Label(self.Shortcut_keys, text="Control + s", font=("Tahoma", 12),
        bg=self.CW["light color"], justify="left", padx=10)
        self.search_key.grid(row=1, column=1, sticky="nswe", pady=5)

        #----------| Settings Label |----------
        self.settings_label = tk.Label(self.Shortcut_keys, text="Settings", font=("Tahoma", 12),
        bg=self.CW["bg color"], justify="left", padx=10)
        self.settings_label.grid(row=1, column=3, sticky="e", pady=5)

        #----------| Settings Key |----------
        self.settings_key = tk.Label(self.Shortcut_keys, text="Control + i", font=("Tahoma", 12),
        bg=self.CW["light color"], justify="left", padx=10)
        self.settings_key.grid(row=1, column=4, sticky="nswe", pady=5)
        self.Shortcut_keys.pack(side="top", fill="x", pady=10)


        self.info_win.mainloop()
        ...

        
    def settings(self) -> None:
        """#--------------------------------------| Settings Window |--------------------------------------
        Display Settings window, in which user can change:
            1. City name, whose weather appears at startup (validate city first)
            2. Units in which temperature is shown.
            3. View from normal to expand.
            4. App display on top or not (normaly view only)."""

        try:    # If settings is already open
            self.settings_win.focus()
            return
        except (AttributeError, tk.TclError):
            pass
        #--------------------------------------| Settings Window |--------------------------------------
        self.settings_win = tk.Toplevel(self, bg=self.CW["bg color"])
        self.settings_win.focus()
        self.settings_win.title("Weather App - Settings")
        self.settings_win.wm_iconbitmap(self.icon)
        self.settings_win.geometry("420x375")
        self.settings_win.minsize(width=420, height=375)
        self.settings_win.maxsize(width=420, height=375)
        self.settings_win.resizable(False, False)

        #--------------------------------------| Settings Label |--------------------------------------
        self.setting_label = tk.Label(self.settings_win, text="Settings", font=("Tahoma", 16, "bold"), bg=self.CW["bg color"], justify="center")
        self.setting_label.pack(side="top", fill="x", pady=5)
        self.set_sep1 = tk.Frame(self.settings_win, bg="black")
        self.set_sep1.pack(side="top", anchor="nw", fill="x", padx=10, pady=5)

        #--------------------------| New Location Label |--------------------------
        self.new_loc_label = tk.LabelFrame(self.settings_win, text="• Update City name to show weather at start",
        font=("Tahoma", 14), bg=self.CW["bg color"], labelanchor="nw", relief="flat")
        #----------| New Location Entry |----------
        self.new_loc = tk.StringVar()
        self.new_loc_entry = tk.Entry(self.new_loc_label, text=self.new_loc, font=("Tahoma", 12), bg=self.CW["light color"],
        relief="solid", highlightthickness=1, highlightbackground="black", justify="center")
        self.new_loc_entry.grid(row=0, column=0, sticky="nswe", ipady=5, padx=10, pady=10)
        self.new_loc.set(self.default_city)
        self.new_loc_entry.bind("<KeyRelease>", lambda e: self.new_loc.set(self.new_loc_entry.get().upper()))

        #----------| New Location Verify button |----------
        self.verified = False
        self.new_loc_verify = tk.Button(self.new_loc_label, text="Verify", font=("Tahoma", 12), bg=self.CW["bg color"],
        relief="solid", overrelief="solid", activebackground=self.CW["light color"], command=self.location_verify)
        self.new_loc_verify.grid(row=0, column=1, sticky="nw", ipadx=10, pady=10, ipady=1)

        self.new_loc_label.pack(side="top", anchor="nw", ipadx=10, padx=10, pady=5)
        self.set_sep2 = tk.Frame(self.settings_win, bg="black")
        self.set_sep2.pack(side="top", anchor="nw", fill="x", padx=10, pady=5)

        #--------------------------| Temperature Unit Label |--------------------------
        self.Temp_label = tk.LabelFrame(self.settings_win, text="• Temperature Unit", font=("Tahoma", 14), bg=self.CW["bg color"],
        labelanchor="nw", relief="flat")
        #----------| Celsius |----------
        self.unit_var = StringVar()
        self.unit_var.set(self._unit)
        self.Celsius_radio = tk.Radiobutton(self.Temp_label, font=("Tahoma", 14), text=self._UNITS["C"][0],
        variable=self.unit_var, value="C", bg=self.CW["bg color"], activebackground=self.CW["light color"],
        selectcolor=self.CW["light color"], relief="flat", overrelief="solid")
        self.Celsius_radio.grid(row=0, column=0, sticky="ne", ipadx=5)

        #----------| Farheniet |----------
        self.Fahreneit_radio = tk.Radiobutton(self.Temp_label, font=("Tahoma", 14), text=self._UNITS["F"][0],
        variable=self.unit_var, value="F", bg=self.CW["bg color"], activebackground=self.CW["light color"],
        selectcolor=self.CW["light color"], relief="flat", overrelief="solid")
        self.Fahreneit_radio.grid(row=0, column=1, sticky="nswe")

        self.Temp_label.pack(side="top", anchor="nw", ipadx=10, padx=10, pady=5)
        self.set_sep3 = tk.Frame(self.settings_win, bg="black")
        self.set_sep3.pack(side="top", anchor="nw", fill="x", padx=10, pady=5)

        #--------------------------| View Label |--------------------------
        self.set_view_label = tk.LabelFrame(self.settings_win, text="• Default View", font=("Tahoma", 14),
        bg=self.CW["bg color"], labelanchor="nw", relief="flat")

        #----------| Normal View |----------
        self.new_view = StringVar()
        self.new_view.set(self.default_view)
        self.normal_view = tk.Radiobutton(self.set_view_label, font=("Tahoma", 14), text="Normal",
        variable=self.new_view, value="normal", bg=self.CW["bg color"],activebackground=self.CW["light color"],
        selectcolor=self.CW["light color"], relief="flat", overrelief="solid")
        self.normal_view.grid(row=0, column=0, sticky="ne", ipadx=5)

        #----------| Expand View |----------
        self.expand_view = tk.Radiobutton(self.set_view_label, font=("Tahoma", 14), text="Expand",
        variable=self.new_view, value="expand", bg=self.CW["bg color"], activebackground=self.CW["light color"],
        selectcolor=self.CW["light color"], relief="flat", overrelief="solid")
        self.expand_view.grid(row=0, column=1, sticky="nw")

        self.set_view_label.pack(side="top", anchor="nw", ipadx=10, padx=10, pady=5)
        self.set_sep4 = tk.Frame(self.settings_win, bg="black")
        self.set_sep4.pack(side="top", anchor="nw", fill="x", padx=10, pady=5)
        
        #--------------------------| Bottom Buttons |--------------------------
        self.buttons_frame = tk.Frame(self.settings_win, bg=self.CW["bg color"])

        self.bottom_sep1 = tk.Frame(self.buttons_frame, bg=self.CW["bg color"])
        self.bottom_sep1.grid(row=0, column=0, padx=60)

        #----------| Apply Button |----------
        self.apply_button = tk.Button(self.buttons_frame, text="Apply", font=("Tahoma", 12), bg=self.CW["bg color"],
        relief="solid", overrelief="solid", activebackground=self.CW["light color"], command=self.apply_settings)
        self.apply_button.grid(row=0, column=1, ipadx=10, padx=10, pady=5)

        #----------| Reset Button |----------
        self.reset_button = tk.Button(self.buttons_frame, text="Reset", font=("Tahoma", 12), bg=self.CW["bg color"],
        relief="solid", overrelief="solid", activebackground=self.CW["light color"], command=self.reset_settings)
        self.reset_button.grid(row=0, column=2, ipadx=10, padx=10, pady=5)

        self.buttons_frame.pack(side="top", fill="x", pady=5)
        
        #--------------------| Bindings |--------------------
        self.new_loc_verify.bind("<Enter>", lambda e: self.new_loc_verify.configure(bg=self.CW["light color"]))
        self.new_loc_verify.bind("<Leave>", lambda e: self.new_loc_verify.configure(bg=self.CW["bg color"]))

        self.Celsius_radio.bind("<Enter>", lambda e: self.Celsius_radio.configure(bg=self.CW["light color"]))
        self.Celsius_radio.bind("<Leave>", lambda e: self.Celsius_radio.configure(bg=self.CW["bg color"]))

        self.Fahreneit_radio.bind("<Enter>", lambda e: self.Fahreneit_radio.configure(bg=self.CW["light color"]))
        self.Fahreneit_radio.bind("<Leave>", lambda e: self.Fahreneit_radio.configure(bg=self.CW["bg color"]))

        self.normal_view.bind("<Enter>", lambda e: self.normal_view.configure(bg=self.CW["light color"]))
        self.normal_view.bind("<Leave>", lambda e: self.normal_view.configure(bg=self.CW["bg color"]))

        self.expand_view.bind("<Enter>", lambda e: self.expand_view.configure(bg=self.CW["light color"]))
        self.expand_view.bind("<Leave>", lambda e: self.expand_view.configure(bg=self.CW["bg color"]))

        self.apply_button.bind("<Enter>", lambda e: self.apply_button.configure(bg=self.CW["light color"]))
        self.apply_button.bind("<Leave>", lambda e: self.apply_button.configure(bg=self.CW["bg color"]))

        self.reset_button.bind("<Enter>", lambda e: self.reset_button.configure(bg=self.CW["light color"]))
        self.reset_button.bind("<Leave>", lambda e: self.reset_button.configure(bg=self.CW["bg color"]))
        self.settings_win.mainloop()


    def update_values(self) -> None:
        """Update all the values and colors in application according to searched city"""

        self.CW = self.current_weather_details()
        self.WF = self.week_forecast_details()
        self.configure(bg=self.CW["bg color"])
        #--------------------------| Search Frame values |--------------------------
        self.Sframe.configure(bg=self.CW["bg color"])
        self.sep_1st.configure(bg=self.CW["bg color"])
        self.city_entry.configure(bg=self.CW["bg color"])
        self.search.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"])
        self.sep_2nd.configure(bg=self.CW["bg color"])
        self.view_button.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"])
        self.info_button.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"])
        self.settings_button.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"])
        
        #--------------------------------------| Search Frame Key Bindings |--------------------------------------
        self.city_entry.bind("<Enter>", lambda e: self.city_entry.configure(relief="solid", bg=self.CW["light color"]))
        self.city_entry.bind("<Leave>", lambda e: self.city_entry.configure(relief="flat", bg=self.CW["bg color"]))
        self.city_entry.bind("<FocusOut>", lambda e: self.city_entry.configure(bg=self.CW["bg color"]))
        try:        # In Some systems it throws ERROR, maybe / not bind
            self.bind_all("</>", lambda e: (self.city_entry.focus(), self.city_entry.select_range(0, tk.END),
            self.city_entry.configure(bg=self.CW["light color"])))
        except tk.TclError:
            pass

        self.search.bind("<Enter>", lambda e: self.search.configure(bg=self.CW["light color"]))
        self.search.bind("<Leave>", lambda e: self.search.configure(bg=self.CW["bg color"]))

        self.view_button.bind("<Enter>", lambda e: self.view_button.configure(bg=self.CW["light color"]))
        self.view_button.bind("<Leave>", lambda e: self.view_button.configure(bg=self.CW["bg color"]))

        self.info_button.bind("<Enter>", lambda e: self.info_button.configure(bg=self.CW["light color"]))
        self.info_button.bind("<Leave>", lambda e: self.info_button.configure(bg=self.CW["bg color"]))
        self.settings_button.bind("<Enter>", lambda e: self.settings_button.configure(bg=self.CW["light color"]))

        self.settings_button.bind("<Leave>", lambda e: self.settings_button.configure(bg=self.CW["bg color"]))

        if self.view=="expand":
            self.open_weather.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"])
            self.open_weather.bind("<Enter>", lambda e: self.open_weather.configure(bg=self.CW["light color"]))
            self.open_weather.bind("<Leave>", lambda e: self.open_weather.configure(bg=self.CW["bg color"]))

        #--------------------------| Current Weather Frame values |--------------------------
        self.current_stats.configure(bg=self.CW["bg color"])
        self.CWFrame.configure(bg=self.CW["bg color"])
        self.CW_main.configure(bg=self.CW["bg color"])

        self.cw_img_frame.configure(text=self.CW["Name"], bg=self.CW["bg color"])
        self.CImg = ImageTk.PhotoImage(Image.open(self.CW["Image"]).resize(self.CW["Image size"]))
        self.cw_img.configure(image=self.CImg, bg=self.CW["bg color"])
        self.cw_img_frame.pack_configure(ipadx=self.CW["ipadx"], ipady=self.CW["ipady"])

        self.cwd_frame.configure(bg=self.CW["bg color"])

        if (self.CW["Temp"] < 0) and (len(str(self.CW["Temp"]))==5):
            self.ctemp = f' -{str(self.CW["Temp"])[1:]}°{self._unit.lower()}'

        elif (len(str(self.CW["Temp"]))==4):
            self.ctemp = f' {str(self.CW["Temp"])}°{self._unit.lower()}'

        else:   self.ctemp = f' {str(self.CW["Temp"])}°{self._unit.lower()}'

        self.CTemp.configure(text=self.ctemp, bg=self.CW["bg color"])
        self.CTime.configure(text=f'{self.CW["Time"]:^11}', bg=self.CW["bg color"])
        self.CDate.configure(text=f'{self.CW["Date"]:^16}', bg=self.CW["bg color"])
        self.Cfeels.configure(text=f"Feels like:{self.CW['Feels']:>10}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.CMin.configure(text=f"Min:\t{self.CW['Min']:>10}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.CMax.configure(text=f"Max:\t{self.CW['Max']:>10}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.CTZone.configure(text=f"GMT {self.CW['Time zone'][:-2] + ':' + self.CW['Time zone'][-2:]}", bg=self.CW["bg color"])
        self.CCity.configure(text=f'{self.CW["City"]:^20}', bg=self.CW["bg color"])

        if (" " in self.CW["Country"]) or (len(self.CW["Country"]) >= 10):
            self.con = self.CW["Country"]
        else:
            self.con = self.CW["Country"] + ", " + self.CW["Region"]
        self.CCon.configure(text=f"{self.con:^20}", bg=self.CW["bg color"])

        self.CW_more.configure(bg=self.CW["bg color"])

        self.CSR.configure(bg=self.CW["bg color"])
        self.CSR_logo.configure(bg=self.CW["bg color"])
        self.CSR_time.configure(text=f'{self.CW["Sunrise"].lower():>12}', bg=self.CW["bg color"])

        self.CSS.configure(bg=self.CW["bg color"])
        self.CSS_logo.configure(bg=self.CW["bg color"])
        self.CSS_time.configure(text=f'{self.CW["Sunset"].lower():>12}', bg=self.CW["bg color"])

        self.CMR.configure(bg=self.CW["bg color"])
        self.CMR_logo.configure(bg=self.CW["bg color"])
        self.CMR_time.configure(text=f'{self.CW["Moonrise"].lower():>12}', bg=self.CW["bg color"])

        self.CMS.configure(bg=self.CW["bg color"])
        self.CMS_logo.configure(bg=self.CW["bg color"])
        self.CMS_time.configure(text=f'{self.CW["Moonset"].lower():>12}', bg=self.CW["bg color"])

        self.CHumid.configure(bg=self.CW["bg color"])
        self.CHumidity_logo.configure(bg=self.CW["bg color"])
        self.CHumid_mark.configure(text=f'{self.CW["Humidity"]:>6}%', bg=self.CW["bg color"])

        self.CVisible.configure(bg=self.CW["bg color"])
        self.CVisible_logo.configure(bg=self.CW["bg color"])
        self.CVisible_mark.configure(text=f'{self.CW["Visibility"]//1000:>7} km', bg=self.CW["bg color"])

        #--------------------------| Week Forecast Frame values |--------------------------
        self.W_WForecast.configure(bg=self.CW["bg color"])
        self.Tomorrow.configure(bg=self.CW["bg color"])
        self.Tomorrow.grid_configure(ipadx=self.WF[0]["Frame ipadx"])
        self.TDate.configure(bg=self.CW["bg color"])
        self.TWeather.configure(text=f'{int(self.WF[0]["Temp"]):>3}°{self._unit.lower()}\n{self.WF[0]["Name"]}',bg=self.CW["bg color"])
        self.Timg = ImageTk.PhotoImage(Image.open(self.WF[0]["Image"]).resize(self.WF[0]["Image size"]))
        self.TW_image.configure(image=self.Timg, bg=self.CW["bg color"])
        self.TW_image.pack_configure(pady=self.WF[0]["Image pady"])
        self.TDay.configure(text=f" {'Day:':<9}{int(self.WF[0]['Day:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.TNight.configure(text=f" {'Night:':<9}{int(self.WF[0]['Night:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])

        self.Day2.configure(bg=self.CW["bg color"])
        self.Day2.grid_configure(ipadx=self.WF[1]["Frame ipadx"])
        self.D2Date.configure(bg=self.CW["bg color"])
        self.D2weather.configure(text=f'{int(self.WF[1]["Temp"]):>3}°{self._unit.lower()}\n{self.WF[1]["Name"]}', bg=self.CW["bg color"])
        self.D2img = ImageTk.PhotoImage(Image.open(self.WF[1]["Image"]).resize(self.WF[1]["Image size"]))
        self.D2w_image.configure(image=self.D2img, bg=self.CW["bg color"])
        self.D2w_image.pack_configure(pady=self.WF[1]["Image pady"])
        self.D2day.configure(text=f" {'Day:':<9}{int(self.WF[1]['Day:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.D2night.configure(text=f" {'Night:':<9}{int(self.WF[1]['Night:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])

        self.Day3.configure(bg=self.CW["bg color"])
        self.Day3.grid_configure(ipadx=self.WF[2]["Frame ipadx"])
        self.D3Date.configure(bg=self.CW["bg color"])
        self.D3weather.configure(text=f'{int(self.WF[2]["Temp"]):>3}°{self._unit.lower()}\n{self.WF[2]["Name"]}', bg=self.CW["bg color"])
        self.D3img = ImageTk.PhotoImage(Image.open(self.WF[2]["Image"]).resize(self.WF[2]["Image size"]))
        self.D3w_image.configure(image=self.D3img, bg=self.CW["bg color"])
        self.D3w_image.pack_configure(pady=self.WF[2]["Image pady"])
        self.D3day.configure(text=f" {'Day:':<9}{int(self.WF[2]['Day:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.D3night.configure(text=f" {'Night:':<9}{int(self.WF[2]['Night:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])

        self.Day4.configure(bg=self.CW["bg color"])
        self.Day4.grid_configure(ipadx=self.WF[3]["Frame ipadx"])
        self.D4Date.configure(bg=self.CW["bg color"])
        self.D4weather.configure(text=f'{int(self.WF[3]["Temp"]):>3}°{self._unit.lower()}\n{self.WF[3]["Name"]}', bg=self.CW["bg color"])
        self.D4img = ImageTk.PhotoImage(Image.open(self.WF[3]["Image"]).resize(self.WF[3]["Image size"]))
        self.D4w_image.configure(image=self.D4img, bg=self.CW["bg color"])
        self.D4w_image.pack_configure(pady=self.WF[3]["Image pady"])
        self.D4day.configure(text=f" {'Day:':<9}{int(self.WF[3]['Day:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.D4night.configure(text=f" {'Night:':<9}{int(self.WF[3]['Night:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])

        self.Day5.configure(bg=self.CW["bg color"])
        self.Day5.grid_configure(ipadx=self.WF[4]["Frame ipadx"])
        self.D5Date.configure(bg=self.CW["bg color"])
        self.D5weather.configure(text=f'{int(self.WF[4]["Temp"]):>3}°{self._unit.lower()}\n{self.WF[4]["Name"]}', bg=self.CW["bg color"])
        self.D5img = ImageTk.PhotoImage(Image.open(self.WF[4]["Image"]).resize(self.WF[4]["Image size"]))
        self.D5w_image.configure(image=self.D5img, bg=self.CW["bg color"])
        self.D5w_image.pack_configure(pady=self.WF[4]["Image pady"])
        self.D5day.configure(text=f" {'Day:':<9}{int(self.WF[4]['Day:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.D5night.configure(text=f" {'Night:':<9}{int(self.WF[4]['Night:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])

        self.Day6.configure(bg=self.CW["bg color"])
        self.Day6.grid_configure(ipadx=self.WF[1]["Frame ipadx"])
        self.D6Date.configure(bg=self.CW["bg color"])
        self.D6weather.configure(text=f'{int(self.WF[5]["Temp"]):>3}°{self._unit.lower()}\n{self.WF[5]["Name"]}', bg=self.CW["bg color"])
        self.D6img = ImageTk.PhotoImage(Image.open(self.WF[5]["Image"]).resize(self.WF[5]["Image size"]))
        self.D6w_image.configure(image=self.D6img, bg=self.CW["bg color"])
        self.D6w_image.pack_configure(pady=self.WF[5]["Image pady"])
        self.D6day.configure(text=f" {'Day:':<9}{int(self.WF[5]['Day:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.D6night.configure(text=f" {'Night:':<9}{int(self.WF[5]['Night:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])

        self.Day7.configure(bg=self.CW["bg color"])
        self.Day7.grid_configure(ipadx=self.WF[1]["Frame ipadx"])
        self.D7Date.configure(bg=self.CW["bg color"])
        self.D7weather.configure(text=f'{int(self.WF[6]["Temp"]):>3}°{self._unit.lower()}\n{self.WF[6]["Name"]}', bg=self.CW["bg color"])
        self.D7img = ImageTk.PhotoImage(Image.open(self.WF[6]["Image"]).resize(self.WF[6]["Image size"]))
        self.D7w_image.configure(image=self.D7img, bg=self.CW["bg color"])
        self.D7w_image.pack_configure(pady=self.WF[6]["Image pady"])
        self.D7day.configure(text=f" {'Day:':<9}{int(self.WF[6]['Day:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.D7night.configure(text=f" {'Night:':<9}{int(self.WF[6]['Night:']):>3}°{self._unit.lower()}", bg=self.CW["bg color"])
        self.week_Forecast.configure(bg=self.CW["bg color"])

        #--------------------------| Current Weather graph colors |--------------------------
        self.CW_graph()
        self.WF_graph()
        self.cw_fig.set_facecolor(self.CW["light color"])
        self.cw_graph.set_facecolor(self.CW["light color"])
        self.cw_annot.set_bbox({"boxstyle" : "round, pad=0.5", "fc" : self.CW["light color"], "ec" : "black", "lw" : 2})

        #--------------------------| Week Forecast graph colors |--------------------------
        self.week_fig.set_facecolor(self.CW["light color"])
        self.week_graph.set_facecolor(self.CW["light color"])
        self.week_annot.set_bbox({"boxstyle" : "round, pad=0.5", "fc" : self.CW["light color"], "ec" : "black", "lw" : 2})
        self.focus()

        #--------------------------------------| Settings colors |--------------------------------------
        try:
            self.settings_win.focus()
            self.settings_win.configure(bg=self.CW["bg color"])
            self.setting_label.configure(bg=self.CW["bg color"])

            self.new_loc_label.configure(bg=self.CW["bg color"])
            self.new_loc_entry.configure(bg=self.CW["light color"])
            self.new_loc_verify.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"])

            self.Temp_label.configure(bg=self.CW["bg color"])
            self.Celsius_radio.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"],
            selectcolor=self.CW["light color"])
            self.Fahreneit_radio.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"],
            selectcolor=self.CW["light color"])

            self.set_view_label.configure(bg=self.CW["bg color"])
            self.normal_view.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"],
            selectcolor=self.CW["light color"])
            self.expand_view.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"],
            selectcolor=self.CW["light color"])

            self.buttons_frame.configure(bg=self.CW["bg color"])
            self.apply_button.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"])
            self.reset_button.configure(bg=self.CW["bg color"], activebackground=self.CW["light color"])

            #--------------------------------------| Settings Key Bindings |--------------------------------------
            self.new_loc_verify.bind("<Enter>", lambda e: self.new_loc_verify.configure(bg=self.CW["light color"]))
            self.new_loc_verify.bind("<Leave>", lambda e: self.new_loc_verify.configure(bg=self.CW["bg color"]))

            self.Celsius_radio.bind("<Enter>", lambda e: self.Celsius_radio.configure(bg=self.CW["light color"]))
            self.Celsius_radio.bind("<Leave>", lambda e: self.Celsius_radio.configure(bg=self.CW["bg color"]))

            self.Fahreneit_radio.bind("<Enter>", lambda e: self.Fahreneit_radio.configure(bg=self.CW["light color"]))
            self.Fahreneit_radio.bind("<Leave>", lambda e: self.Fahreneit_radio.configure(bg=self.CW["bg color"]))

            self.normal_view.bind("<Enter>", lambda e: self.normal_view.configure(bg=self.CW["light color"]))
            self.normal_view.bind("<Leave>", lambda e: self.normal_view.configure(bg=self.CW["bg color"]))

            self.expand_view.bind("<Enter>", lambda e: self.expand_view.configure(bg=self.CW["light color"]))
            self.expand_view.bind("<Leave>", lambda e: self.expand_view.configure(bg=self.CW["bg color"]))

            self.apply_button.bind("<Enter>", lambda e: self.apply_button.configure(bg=self.CW["light color"]))
            self.apply_button.bind("<Leave>", lambda e: self.apply_button.configure(bg=self.CW["bg color"]))

            self.reset_button.bind("<Enter>", lambda e: self.reset_button.configure(bg=self.CW["light color"]))
            self.reset_button.bind("<Leave>", lambda e: self.reset_button.configure(bg=self.CW["bg color"]))
        except (AttributeError, tk.TclError):
            pass

        #--------------------------------------| Info Window |--------------------------------------
        try:
            self.info_win.focus()
            self.info_win.configure(bg=self.CW["bg color"])
            self.info.configure(bg=self.CW["bg color"])

            self.dev_detail.configure(bg=self.CW["bg color"])
            self.dev_github.configure(bg=self.CW["bg color"], activebackground=self.CW["bg color"],)

            self.WA_details.configure(bg=self.CW["bg color"])
            self.wa_start.configure(bg=self.CW["bg color"])
            self.current_api_button.configure(bg=self.CW["bg color"], activebackground=self.CW["bg color"],)
            self.one_call_api_button.configure(bg=self.CW["bg color"], activebackground=self.CW["bg color"],)
            self.OW_logo.configure(bg=self.CW["bg color"])
            self.wa_extra.configure(bg=self.CW["bg color"])

            self.Shortcut_keys.configure(bg=self.CW["bg color"])
            self.info_label.configure(bg=self.CW["bg color"])
            self.info_key.configure(bg=self.CW["light color"])
      
            self.layout_label.configure(bg=self.CW["bg color"])
            self.layout_key.configure(bg=self.CW["light color"])

            self.search_label.configure(bg=self.CW["bg color"])
            self.search_key.configure(bg=self.CW["light color"])

            self.settings_label.configure(bg=self.CW["bg color"])
            self.settings_key.configure(bg=self.CW["light color"])

            self.OW_logo.bind("<Enter>", lambda e: self.OW_logo.configure(bg=self.CW["light color"]))
            self.OW_logo.bind("<Leave>", lambda e: self.OW_logo.configure(bg=self.CW["bg color"]))
        except (AttributeError, tk.TclError):
            pass


    def Search_Weather(self, event=None) -> None:
        """--------------------------| Search Weather |--------------------------
        Search the weather upon clicking Enter key or clicking search button.
        If application started first time, then search weather of default city.
        Display weather and graph, if wrong city name, then show a message."""

        self.city.set(self.city.get().upper())
        self.Search_city = self.city.get().strip()
        if (not self.Search_city.isalpha()) and not ((" " in self.Search_city) or ("-" in self.Search_city) or ("'" in self.Search_city)):
            messagebox.showerror(title="Invalid City Name", message="Please Enter Alphabetic Characters Only!")
            self.city.set("")
            return
        
        self.exit_code = self.get_forecast(self.Search_city)
        if self.exit_code==0:
            try:
                if self.start:
                    self.start = False
                    self.Weather_Frames()
                    self.CW_Frame()
                    self.WF_Frame()
                    self.CW_graph()
                    self.WF_graph()

                self.update_values()

                if self.state=="disabled":
                    self.change_button_state()

                self.after(1000, lambda : self.date_time_update())
                # 1st time values update after 5 min
                self.after(300000, lambda : self.temp_update())

                if self.view=="normal":
                    self.side_sep.configure(bg=self.Sframe.cget("bg"))
            except tk.TclError:
                pass        # Sometimes, while updating weather, date_time_update() or temp_update() throw TclError due to no time or weather found.
            except Exception as e:  # Any unknwon exception
                messagebox.showerror(title="Unkown Error: Weather App",message=f"An Unkown Error occurred!\nPlease search the weather again,\
or click 'OK'.\nPlease report this error to the developer with the screenshot attached.\n\nError:\n{e}")
        
        elif self.exit_code==1:
            messagebox.showerror(title="Error: 1 Weather App",
            message="No Internet Connection found!\nPlease connect to the Internet to search weather.")
        
        elif self.exit_code==2:
            retry = messagebox.askretrycancel(title="Error: 2 Weather App",
            message="The Website (openweather) is taking too much to respond.\nPress Retry to retry after 10 seconds.\nThank you.")
            if retry:
                self.after(10000, self.Search_Weather)

        elif self.exit_code==3:
            messagebox.showerror(title="Error: 3 Weather App", message=f"Invalid City Name: '{self.Search_city}'!\
\nMaybe,\n• You have entered wrong City name, or\n• City name is not present in list of openweather.org")
            self.city.set("")

        return


    def change_button_state(self) -> None:
        """Change the state of buttons in search bar, after weather updates, the state changed to normal."""
        try:
            if self.state=="disabled":
                self.state = "normal"
                self.search.configure(state="normal")
                self.view_button.configure(state="normal")
                self.info_button.configure(state="normal")
                self.settings_button.configure(state="normal")
                self.open_weather.configure(state="normal")
            else:
                self.state = "disabled"
                self.search.configure(state="disabled")
                self.view_button.configure(state="disabled")
                self.info_button.configure(state="disabled")
                self.settings_button.configure(state="disabled")
                self.open_weather.configure(state="disabled")
        except (AttributeError, tk.TclError):
            pass
    

    def switch_layout(self) -> None:
        """--------------------------| Switch layout at button pressed |--------------------------
        If layout is small (normal) then, switches to large (expand) & vice-versa.
        Also change the configuration of search bar."""

        if self.view=="normal":
            #---------------| Switch from Normal to Expand |---------------
            self.view = "expand"
            self.width = 1730
            self.height = 800
            self.geometry(f"{self.width}x{self.height}+{self.winfo_screenwidth()//20}+100")

            self.Sframe.pack_configure(ipady=2)
            self.sep_1st.grid_configure(ipadx=360)
            self.city_entry.configure(font=("Tahoma", 18, "bold"), bd=2, width=20)
            self.city_entry.grid_configure(ipady=5)

            self.search_img = ImageTk.PhotoImage(Image.open("./assets/search.png").resize((38, 38)))
            self.search.configure(image=self.search_img)

            self.sep_2nd.grid_configure(ipadx=180)
            self.view_img = ImageTk.PhotoImage(Image.open("./assets/uparrowhead.png").resize((26, 26)))
            self.view_button.configure(image=self.view_img)
            self.view_button.grid_configure(ipady=6)

            self.info_img = ImageTk.PhotoImage(Image.open("./assets/info.png").resize((36, 36)))
            self.info_button.configure(image=self.info_img)
            self.info_button.grid_configure(ipady=1, padx=18)

            self.settings_img = ImageTk.PhotoImage(Image.open("./assets/settings.png").resize((30, 30)))
            self.settings_button.configure(image=self.settings_img)
            self.settings_button.grid_configure(ipadx=2, ipady=4)

            self.open_WImg = ImageTk.PhotoImage(Image.open("./assets/open_weather_logo.png").resize((100, 38)))
            self.open_weather = tk.Button(self.Sframe, image=self.open_WImg, bg=self.CW["bg color"], 
            relief="flat", overrelief="solid", command=self.open_weather_link)
            self.open_weather.grid(row=0, column=7, ipadx=5, padx=10)
            self.open_weather.bind("<Enter>", lambda e: self.open_weather.configure(bg=self.CW["light color"]))
            self.open_weather.bind("<Leave>", lambda e: self.open_weather.configure(bg=self.CW["bg color"]))

            # removing timezone, changing separator color in normal
            self.CTZone.grid(row=3, column=3, sticky="nswe")
            self.CCity.grid(row=4, column=3, sticky="nswe")
            self.CCon.grid(row=5, column=3, sticky="nswe")
            self.side_sep.configure(bg="blacK")

        else:
            #---------------| Switch from Expand to Normal |---------------
            self.view = "normal"
            self.width = 700
            self.height = 260
            self.geometry(f"{self.width}x{self.height}+{self.winfo_screenwidth()//3}+50")

            self.Sframe.pack_configure(ipady=1)
            self.sep_1st.grid_configure(ipadx=110)
            self.city_entry.configure(font=("Tahoma", 16, "bold"), bd=2, width=15)
            self.city_entry.grid_configure(ipady=3)

            self.search_img = ImageTk.PhotoImage(Image.open("./assets/search.png").resize((30, 31)))
            self.search.configure(image=self.search_img)

            self.sep_2nd.grid_configure(ipadx=50)
            self.view_img = ImageTk.PhotoImage(Image.open("./assets/downarrowhead.png").resize((20, 20)))
            self.view_button.configure(image=self.view_img)
            self.view_button.grid_configure(ipady=5)

            self.info_img = ImageTk.PhotoImage(Image.open("./assets/info.png").resize((30, 30)))
            self.info_button.configure(image=self.info_img)
            self.info_button.grid_configure(padx=10, ipady=0)

            self.settings_img = ImageTk.PhotoImage(Image.open("./assets/settings.png").resize((25, 26)))
            self.settings_button.configure(image=self.settings_img)
            self.settings_button.grid_configure(ipadx=2, ipady=2)
            
            try:
                self.open_weather.destroy()
            except AttributeError:
                pass

            # Adding timezone, changing separator color in expand
            self.CTZone.grid_forget()
            self.CCity.grid(row=3, column=3, sticky="nswe")
            self.CCon.grid(row=4, column=3, sticky="nswe")
            self.side_sep.configure(bg=self.CW["bg color"])

        self.minsize(width=self.width, height=self.height)
        self.maxsize(width=self.width, height=self.height)
        self.update()


    def date_time_update(self) -> None:
        """Updates the time and date after 0.5(half) second."""
        try:
            self.new_time = datetime.datetime.now(pytz.timezone(self.location_details()[-1])).strftime("%I:%M %p")
            self.new_date = datetime.datetime.now(pytz.timezone(self.location_details()[-1])).strftime("%a, %d %b' %y")

            self.CTime.configure(text=f'{self.new_time:^11}')
            self.CDate.configure(text=f'{self.new_date:^16}')
            
            self.after(500, self.date_time_update)
        except KeyError:    # If wrong city entered but time is moving accordingly
            pass


    def temp_update(self) -> None:
        """Updates all the values after 5 minuters."""

        self.update_values()
        self.after(300000, self.temp_update)

    
    def github_link(self) -> None:
        """Open Github profile page
        https://github.com/Param302 in web browser."""

        webbrowser.open_new_tab("https://github.com/Param302")


    def current_api_link(self) -> None:
        """Open Current Weather Data API of openweathermap.org
        https://openweathermap.org/current in web browser."""

        webbrowser.open_new_tab("https://openweathermap.org/current")


    def one_call_api_link(self) -> None:
        """Open One Call API of openweathermap.org
        https://openweathermap.org/api/one-call-api in web browser."""

        webbrowser.open_new_tab("https://openweathermap.org/api/one-call-api")


    def open_weather_link(self) -> None:
        """Open Homepage of open weather website.
        https://openweathermap.org/ in web browser."""

        webbrowser.open_new_tab("https://openweathermap.org/")
        

    def location_verify(self) -> None:
        """--------------------| Check New Location |--------------------
        Search entered location in settings and check whether the location is correct or not."""

        confirm = False
        self.search_new_loc = self.new_loc_entry.get().strip()
        if (not self.search_new_loc.isalpha()) and not ((" " in self.search_new_loc) or ("-" in self.search_new_loc) or ("'" in self.search_new_loc)):
            messagebox.showerror(title="Invalid City Name", message="Please Enter Alphabetic Characters Only!")
            self.new_loc.set(self.default_city)
            self.settings_win.focus()
            return

        try:
            new_loc_req = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={self.search_new_loc}\
&appid={self._API}&units={self._UNITS[self._unit][1]}", timeout=15)

        except requests.exceptions.ConnectionError:     # No Internet
            messagebox.showerror(title="Error: 1 Weather App", message="No Internet Connection found!\
                \nPlease connect to the Internet to search weather.")
            self.new_loc.set(self.default_city)

        except requests.Timeout:                        # response time out
            messagebox.showinfo(title="Error: 2 Weather App",
            message="The Website (openweather) is taking too much to respond.\nPlease try again later.\nThank you.")
            self.after(10000, self.Search_Weather)
            self.new_loc.set(self.default_city)

        else:
            new_loc_json = new_loc_req.json()
            try:        # Fetching temp to check for correct location
                new_loc_json["main"]["temp"]
                confirm = True
                messagebox.showinfo(title="Weather App", message="\tCity Verified!\t")


            except KeyError:    # location is not correct
                messagebox.showerror(title="Error: 3 Weather App", message=f"Invalid City Name: '{self.search_new_loc}'!\
\nMaybe,\n• You have entered wrong City name, or\n• City name is not present in list of openweather.org")
                self.new_loc.set(self.default_city)

        if confirm: self.verified = True
        self.settings_win.focus()
        return


    def apply_settings(self) -> None:
        """--------------------| Apply Settings |--------------------
        If Apply button pressed, all modified values will updated."""

        if (not self.verified) and (self.new_loc_entry.get().strip()!=self.default_city):
            messagebox.showwarning("Weather App", message="Please Verify the location first")
            return

        with open("./assets/location.txt", "w+") as loc:
            loc.write(self.new_loc_entry.get().strip())
            loc.seek(0)
            self.default_city = loc.read()

        with open("./assets/unit.txt", "w+") as u:
            u.write(self.unit_var.get())
            u.seek(0)
            self._unit = u.read()
            self.Search_Weather()

        with open("./assets/view.txt", "w+") as v:
            v.write(self.new_view.get())
            v.seek(0)
            self.default_view = v.read()
                    
        self.settings_win.focus()
        return


    def reset_settings(self) -> None:
        """--------------------| Reset Settings |--------------------
        If Reset button pressed, all values will be reset."""

        with open("./assets/location.txt", "w+") as loc:
            self.new_loc.set("NEW DELHI")
            loc.write(self.new_loc_entry.get().strip())
            loc.seek(0)
            self.default_city = loc.read()

        with open("./assets/unit.txt", "w+") as u:
            self.unit_var.set("C")
            u.write(self.unit_var.get())
            u.seek(0)
            self._unit = u.read()
        
        with open("./assets/view.txt", "w+") as v:
            self.new_view.set("normal")
            v.write(self.new_view.get())
            v.seek(0)
            self.default_view = v.read()

        self.settings_win.focus()
        return


if __name__ == "__main__":
    my_app = WeatherApp()
    my_app.mainloop()

#====================================================| THE END |====================================================
