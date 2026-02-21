globals [ critical-time critical-time-list adopter-list ]

turtles-own [ act att theta time object ]

to startup
   setup
end

to setup
   clear
   set critical-time 0
   setup-social-network
   setup-agent-population
end

to clear
   reset-ticks
   clear-turtles
   clear-patches
   clear-drawing
   clear-all-plots
   clear-output
   random-seed new-seed   
end
       
to setup-social-network
   no-display
   set-default-shape turtles "circle"
   ifelse (network-type = "SFN") [ setup-scale-free-network ] [ setup-small-world-network ]
   ask-concurrent links [ set color gray - 3 ]
   display
   plot-network-degree-distribution
end

to setup-scale-free-network
   make-node nobody 
   make-node turtle 0
   repeat 398 [ make-node find-partner ]
   add-link 0
   foreach shuffle n-values 400 [ ? ] [ repeat 3 [ add-link ? ] ]
   set-posXY-of-nodes
end

to make-node [ old-node ]
   create-turtles 1 [         
          set size 0.3
          if (old-node != nobody) [ create-link-with old-node ]
   ]
end

to-report find-partner
   let total random sum [ count link-neighbors ] of turtles
   let partner nobody
   ask turtles [
       let nc count link-neighbors
       if (partner = nobody) [ ifelse (nc > total) [ set partner self ] [ set total total - nc ] ]
   ]
   report partner
end

to add-link [ self-no ]
   let pass false
   while [ pass = false ] [
         let partner find-partner
         while [ partner = turtle self-no] [ set partner find-partner ]
         ask turtle self-no [ 
             if (not link-neighbor? partner) [ 
                create-link-with partner
                set pass true
             ]
         ] 
   ]
end

to set-posXY-of-nodes
   let nowx 0
   let nowy 0
   ask turtles [
       setxy nowx nowy
       set nowx nowx + 1
       set nowy nowy + int(nowx / world-width)
       set nowx nowx mod world-width
   ]   
end

to setup-small-world-network
   ask-concurrent patches [ sprout 1 [ set size 0.3 ] ]
   ask-concurrent turtles [ create-links-with turtles-on neighbors ]
   ask-concurrent links [
       let rewired? false
       if (random-float 1) < rewiring-probability [
          let node1 end1
          ask node1 [
              if ([ count link-neighbors ] of node1 < (count turtles - 1)) [
                 create-link-with one-of turtles with [ (self != node1) and (not link-neighbor? node1) ] [ set rewired? true ]
              ]
          ]
          if (rewired?) [ die ]
       ]       
   ]
end

to plot-network-degree-distribution
   set-current-plot "Node degree distribution"
   plot-pen-reset
   ifelse (network-type = "SFN") [ plot-SFN-degree-distribution ] [ plot-SWN-degree-distribution ] 
end

to plot-SWN-degree-distribution
   set-plot-pen-mode 1
   let max-degree max [ count link-neighbors ] of turtles
   let min-degree min [ count link-neighbors ] of turtles                                                       
   set-plot-x-range min-degree max-degree + 1                        
   histogram [ count link-neighbors ] of turtles
end

to plot-SFN-degree-distribution
   set-plot-pen-mode 2
   let degree 1
   let max-degree max [ count link-neighbors ] of turtles
   while [ degree <= max-degree ] [
         let matches turtles with [ count link-neighbors = degree ]
         if (any? matches) [ plotxy log degree 10 log (count matches) 10 ]
         set degree degree + 1
   ]
end

to setup-agent-population
   ask-concurrent turtles [
       ; set att   round(abs(random-normal avg-of-attitudes  std-of-attitudes))  mod 100 + 1
       set att   max list 1 (min list 100 random-normal avg-of-attitudes  std-of-attitudes)
       ; set theta round(abs(random-normal avg-of-thresholds std-of-thresholds)) mod 100 + 1
       set theta max list 1 (min list 100 random-normal avg-of-thresholds std-of-thresholds)
       become-susceptible
   ]
   ask-concurrent chosen-leaders [
       set att   100
       set theta   0
       become-action
   ]
   plot-theta-distribution
   plot-att-distribution
end

to-report chosen-leaders 
   report ifelse-value (clustered-pioneers? = true) [ max-n-of no-of-pioneers turtles [ xcor + ycor ] ] [ n-of no-of-pioneers turtles ]
end

to plot-theta-distribution
   set-current-plot "Threshold distribution"
   plot-pen-reset                                                    
   set-plot-x-range 1 ifelse-value (avg-of-thresholds = 100) [101] [100]                       
   histogram [ theta ] of turtles
end

to plot-att-distribution
   set-current-plot "Attitude distribution"
   plot-pen-reset                                                    
   set-plot-x-range 1 ifelse-value (avg-of-attitudes = 100) [101] [100]                        
   histogram [ att ] of turtles
end

to go [ exp-ID ]
   setup
  ;if (exp-ID > 0) [ movie-grab-view ]
   while [ ticks < max-time ] [
         ask-concurrent turtles [ communicate-and-make-decision ]
         update-plot
         if (exp-ID > 0) [
           ;movie-grab-view ; 太佔空間，除非必要，否則不要使用。
            file-print (word exp-ID ":" ticks ":act:" count turtles with [ act ] ":" count turtles with [ not act ] ":att:" mean [ att ] of turtles ":" standard-deviation [ att ] of turtles)
         ]
         if (exp-ID > 0) [ set adopter-list replace-item ticks adopter-list (item ticks adopter-list + (count turtles with [ act ] * (1.0 / no-of-experiments))) ]
         tick
   ]
   if (exp-ID > 0) [
      file-print (word "critical-point:" critical-time)
      set critical-time-list lput critical-time critical-time-list
   ]
end

to communicate-and-make-decision
   set object one-of link-neighbors
   if (object != nobody) [ communicate ([ act ] of object) act ([ att ] of object) att ]
   make-decision  
end

to communicate [ A1 A2 B C ]
   if (A1  = true and A2 != true and abs(C - B) < bounded-confidence) [ ifelse (B > C) [ change-opinion-2 B C ] [ change-opinion-1 B C ] ] ; 隔壁已採用, 本身未採用, 若隔壁態度比我正面, 單向說服, 若隔壁態度比我負面, 雙向溝通
   if (A1 != true and A2  = true and abs(C - B) < bounded-confidence) [ ifelse (B > C) [ change-opinion-1 B C ] [ change-opinion-3 B C ] ] ; 自己已採用, 隔壁未採用, 若隔壁態度比我正面, 雙向溝通, 若隔壁態度比我負面, 單向說服
   if (A1  = true and A2  = true and abs(C - B) < bounded-confidence) [ ifelse (B > C) [ change-opinion-2 B C ] [ change-opinion-3 B C ] ] ; 隔壁和自己皆採用, 態度變得更正面                                      
   if (A1 != true and A2 != true and abs(C - B) < bounded-confidence)                  [ change-opinion-1 B C ]                            ; 自己和隔壁皆未採用, 雙向溝通, 拉近距離
end

to change-opinion-1 [ B C ]
   set   att             round((C + convergence-rate * (B - C)))
   set [ att ] of object round((B + convergence-rate * (C - B)))
end
         
to change-opinion-2 [ B C ]
   set   att             round((C + convergence-rate * (B - C)))
end

to change-opinion-3 [ B C ]
   set [ att ] of object round((B + convergence-rate * (C - B)))
end

to make-decision
   ifelse (act = false and att > 50 and count link-neighbors != 0 and count link-neighbors with [ act = true ] / count link-neighbors >= theta / 100) [ become-action ] [ set-agent-color ]
end

to become-action
   set act  true
   set time ticks
   set-agent-color
end
  
to become-susceptible
   set act false
   set-agent-color
end

to set-agent-color
   ifelse (act = true) [ set color red ] [ set color scale-color green att 100 1 ]
end

to update-plot
   set-current-plot "Adoption dynamics"
   set-plot-y-range 0 count turtles
   set-plot-x-range 1 max-time
   set-current-plot-pen "Not-yet-adopter"
   plot (count turtles with [ not act ])
   set-current-plot-pen "Adopter"
   plot (count turtles with [ act ])
   
   set-current-plot "New adopter dynamics"
   set-plot-x-range 1 max-time
   set-current-plot-pen "New adopter"
   if (plot-y-max < count turtles with [ act and time = ticks ]) [ set-plot-y-range 0 count turtles with [ act and time = ticks ] ]
   plot round(count turtles with [ act and time = ticks ])
   
   set-current-plot "Attitude trajectory"
   set-plot-y-range 1 100
   set-plot-x-range 1 max-time
   let color-spectrum [ 9 pink red orange brown yellow green lime turquoise cyan sky blue violet magenta black ]
   let attitude 1
   while [ attitude <= 100 ] [
         let no count turtles with [ att = attitude ]
         if (no > 0) [
            let color-index round(log no 2 * ((length color-spectrum - 1) / log count turtles 2))
            set-plot-pen-color item color-index color-spectrum
            plotxy ticks attitude
         ]
         set attitude attitude + 1
   ]
   plot-att-distribution   
end

to-report critical-point
   ifelse (critical-time > 0) [ report critical-time ] [ ifelse (count turtles with [ act ] > count turtles with [ not act ]) [ set critical-time ticks ] [ set critical-time 0 ] report critical-time ]
end

to run-100-experiments 
   let world-directory user-directory
   if (world-directory != false) [
      set-current-directory world-directory
      set critical-time-list []
      set adopter-list []
      repeat max-time [ set adopter-list lput 0 adopter-list ]
      let exp-no 1
      while [ exp-no <= no-of-experiments ] [
            print (word "exp: " exp-no)
            file-open (word "experiment-" exp-no ".txt")
           ;movie-start (word "experiment-" exp-no ".mov")
            go exp-no
           ;movie-close
            file-close
            export-interface (word "experiment-" exp-no "-interface.png")
            export-world (word "experiment-" exp-no "-world")
            set exp-no exp-no + 1
      ]
      let index 0
      while [ index < max-time ] [ 
            set adopter-list replace-item index adopter-list round(item index adopter-list)
            set index index + 1
      ]
      file-open "experiment.txt"
      file-print (word "critical-points:" critical-time-list)
      file-print (word "adopters:"        adopter-list)
      file-close
   ]
end

to import-simulation
   clear-all
   let world-file user-file
   if (world-file != false) [ import-world world-file ]
end
@#$#@#$#@
GRAPHICS-WINDOW
850
10
1290
471
-1
-1
21.5
1
10
1
1
1
0
1
1
1
0
19
0
19
1
1
1
time steps

CC-WINDOW
5
712
1299
807
Command Center
0

PLOT
220
457
842
577
Adoption dynamics
Time
Agent
1.0
100.0
0.0
100.0
false
true
PENS
"Adopter" 1.0 0 -2674135 true
"Not-yet-adopter" 1.0 0 -10899396 true

MONITOR
780
374
842
423
Adopter
count turtles with [ act = true ]
17
1
12

SLIDER
40
50
211
83
no-of-pioneers
no-of-pioneers
0
100
5
1
1
NIL
HORIZONTAL

BUTTON
40
11
142
44
Experiments
run-100-experiments
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL

BUTTON
145
11
211
44
Run once
go 0
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL

PLOT
1070
472
1290
698
Node degree distribution
Degree
Node
0.0
0.0
0.0
0.0
true
false
PENS
"default" 1.0 1 -2674135 false

PLOT
220
10
780
457
Attitude trajectory
Time
Attitude
1.0
100.0
1.0
100.0
false
false
PENS
"default" 1.0 2 -2674135 true

MONITOR
780
10
842
59
PA
count turtles with [ att > 50 and att <= 100 ]
17
1
12

MONITOR
780
147
842
196
NA
count turtles with [ att <= 50 and att > 0 ]
17
1
12

SLIDER
40
248
212
281
avg-of-thresholds
avg-of-thresholds
10
100
40
5
1
NIL
HORIZONTAL

SLIDER
40
115
211
148
bounded-confidence
bounded-confidence
0
90
50
10
1
NIL
HORIZONTAL

SLIDER
40
358
212
391
rewiring-probability
rewiring-probability
0.00
1.00
0
0.05
1
NIL
HORIZONTAL

SLIDER
40
280
212
313
std-of-thresholds
std-of-thresholds
0.0
30.0
10
5.0
1
NIL
HORIZONTAL

SWITCH
40
83
211
116
clustered-pioneers?
clustered-pioneers?
0
1
-1000

SLIDER
40
149
212
182
convergence-rate
convergence-rate
0.1
1
0.1
0.1
1
NIL
HORIZONTAL

SLIDER
40
390
212
423
max-time
max-time
50
1000
300
50
1
NIL
HORIZONTAL

SLIDER
40
182
212
215
avg-of-attitudes
avg-of-attitudes
10
100
50
10
1
NIL
HORIZONTAL

SLIDER
40
215
212
248
std-of-attitudes
std-of-attitudes
0
30
10
5
1
NIL
HORIZONTAL

MONITOR
780
285
842
330
Links
count links
17
1
11

PLOT
40
457
212
696
Attitude distribution
Attitude
Agent
1.0
100.0
0.0
10.0
true
false
PENS
"default" 1.0 1 -2674135 true

PLOT
220
577
842
697
New adopter dynamics
Time
Agent
1.0
100.0
0.0
10.0
false
true
PENS
"New adopter" 1.0 0 -955883 true

MONITOR
780
330
842
375
Critical
critical-point
17
1
11

BUTTON
780
424
843
458
Load
import-simulation
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL

SLIDER
40
424
211
457
no-of-experiments
no-of-experiments
10
1000
20
10
1
NIL
HORIZONTAL

PLOT
850
472
1070
698
Threshold distribution
Threshold
Agent
1.0
100.0
0.0
10.0
true
false
PENS
"default" 1.0 1 -2674135 true

MONITOR
780
58
842
103
Avg PA
mean [ att ] of turtles with [att > 50 and att <= 100]
2
1
11

MONITOR
780
195
842
240
Avg NA
ifelse-value (count turtles with [ att <= 50 and att > 0 ] = 0) [0] [mean [ att ] of turtles with [ att >= 0 and att < 50 ]]
2
1
11

MONITOR
780
103
842
148
Std PA
standard-deviation [ att ] of turtles with [ att > 50 and att <= 100 ]
2
1
11

MONITOR
780
239
842
284
Std NA
ifelse-value (count turtles with [ att <= 50 and att > 0 ] = 0) [ 0 ] [ standard-deviation [ att ] of turtles with [ att < 50 ] ]
2
1
11

CHOOSER
40
314
212
359
network-type
network-type
"SFN" "SWN/RN/CA"
1

@#$#@#$#@
WHAT IS IT?
-----------
This section could give a general understanding of what the model is trying to show or explain.

叫好不叫座的英文翻譯
------------
best game no one played
loud thunder, but small raindrops
good film, but small audience
best product/car/xxx no one bought.


HOW IT WORKS
------------
This section could explain what rules the agents use to create the overall behavior of the model.


HOW TO USE IT
-------------
This section could explain how to use the model, including a description of each of the items in the interface tab.


THINGS TO NOTICE
----------------
This section could give some ideas of things for the user to notice while running the model.


THINGS TO TRY
-------------
This section could give some ideas of things for the user to try to do (move sliders, switches, etc.) with the model.


EXTENDING THE MODEL
-------------------
This section could give some ideas of things to add or change in the procedures tab to make the model more complicated, detailed, accurate, etc.


NETLOGO FEATURES
----------------
This section could point out any especially interesting or unusual features of NetLogo that the model makes use of, particularly in the Procedures tab.  It might also point out places where workarounds were needed because of missing features.


RELATED MODELS
--------------
This section could give the names of models in the NetLogo Models Library or elsewhere which are of related interest.


CREDITS AND REFERENCES
----------------------
This section could contain a reference to the model's URL on the web if it has one, as well as any other necessary credits or references.
@#$#@#$#@
default
true
0
Polygon -7500403 true true 150 5 40 250 150 205 260 250

airplane
true
0
Polygon -7500403 true true 150 0 135 15 120 60 120 105 15 165 15 195 120 180 135 240 105 270 120 285 150 270 180 285 210 270 165 240 180 180 285 195 285 165 180 105 180 60 165 15

arrow
true
0
Polygon -7500403 true true 150 0 0 150 105 150 105 293 195 293 195 150 300 150

box
false
0
Polygon -7500403 true true 150 285 285 225 285 75 150 135
Polygon -7500403 true true 150 135 15 75 150 15 285 75
Polygon -7500403 true true 15 75 15 225 150 285 150 135
Line -16777216 false 150 285 150 135
Line -16777216 false 150 135 15 75
Line -16777216 false 150 135 285 75

bug
true
0
Circle -7500403 true true 96 182 108
Circle -7500403 true true 110 127 80
Circle -7500403 true true 110 75 80
Line -7500403 true 150 100 80 30
Line -7500403 true 150 100 220 30

butterfly
true
0
Polygon -7500403 true true 150 165 209 199 225 225 225 255 195 270 165 255 150 240
Polygon -7500403 true true 150 165 89 198 75 225 75 255 105 270 135 255 150 240
Polygon -7500403 true true 139 148 100 105 55 90 25 90 10 105 10 135 25 180 40 195 85 194 139 163
Polygon -7500403 true true 162 150 200 105 245 90 275 90 290 105 290 135 275 180 260 195 215 195 162 165
Polygon -16777216 true false 150 255 135 225 120 150 135 120 150 105 165 120 180 150 165 225
Circle -16777216 true false 135 90 30
Line -16777216 false 150 105 195 60
Line -16777216 false 150 105 105 60

car
false
0
Polygon -7500403 true true 300 180 279 164 261 144 240 135 226 132 213 106 203 84 185 63 159 50 135 50 75 60 0 150 0 165 0 225 300 225 300 180
Circle -16777216 true false 180 180 90
Circle -16777216 true false 30 180 90
Polygon -16777216 true false 162 80 132 78 134 135 209 135 194 105 189 96 180 89
Circle -7500403 true true 47 195 58
Circle -7500403 true true 195 195 58

circle
false
0
Circle -7500403 true true 0 0 300

circle 2
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240

cow
false
0
Polygon -7500403 true true 200 193 197 249 179 249 177 196 166 187 140 189 93 191 78 179 72 211 49 209 48 181 37 149 25 120 25 89 45 72 103 84 179 75 198 76 252 64 272 81 293 103 285 121 255 121 242 118 224 167
Polygon -7500403 true true 73 210 86 251 62 249 48 208
Polygon -7500403 true true 25 114 16 195 9 204 23 213 25 200 39 123

cylinder
false
0
Circle -7500403 true true 0 0 300

dot
false
0
Circle -7500403 true true 90 90 120

face happy
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 255 90 239 62 213 47 191 67 179 90 203 109 218 150 225 192 218 210 203 227 181 251 194 236 217 212 240

face neutral
false
0
Circle -7500403 true true 8 7 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Rectangle -16777216 true false 60 195 240 225

face sad
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 168 90 184 62 210 47 232 67 244 90 220 109 205 150 198 192 205 210 220 227 242 251 229 236 206 212 183

fish
false
0
Polygon -1 true false 44 131 21 87 15 86 0 120 15 150 0 180 13 214 20 212 45 166
Polygon -1 true false 135 195 119 235 95 218 76 210 46 204 60 165
Polygon -1 true false 75 45 83 77 71 103 86 114 166 78 135 60
Polygon -7500403 true true 30 136 151 77 226 81 280 119 292 146 292 160 287 170 270 195 195 210 151 212 30 166
Circle -16777216 true false 215 106 30

flag
false
0
Rectangle -7500403 true true 60 15 75 300
Polygon -7500403 true true 90 150 270 90 90 30
Line -7500403 true 75 135 90 135
Line -7500403 true 75 45 90 45

flower
false
0
Polygon -10899396 true false 135 120 165 165 180 210 180 240 150 300 165 300 195 240 195 195 165 135
Circle -7500403 true true 85 132 38
Circle -7500403 true true 130 147 38
Circle -7500403 true true 192 85 38
Circle -7500403 true true 85 40 38
Circle -7500403 true true 177 40 38
Circle -7500403 true true 177 132 38
Circle -7500403 true true 70 85 38
Circle -7500403 true true 130 25 38
Circle -7500403 true true 96 51 108
Circle -16777216 true false 113 68 74
Polygon -10899396 true false 189 233 219 188 249 173 279 188 234 218
Polygon -10899396 true false 180 255 150 210 105 210 75 240 135 240

house
false
0
Rectangle -7500403 true true 45 120 255 285
Rectangle -16777216 true false 120 210 180 285
Polygon -7500403 true true 15 120 150 15 285 120
Line -16777216 false 30 120 270 120

leaf
false
0
Polygon -7500403 true true 150 210 135 195 120 210 60 210 30 195 60 180 60 165 15 135 30 120 15 105 40 104 45 90 60 90 90 105 105 120 120 120 105 60 120 60 135 30 150 15 165 30 180 60 195 60 180 120 195 120 210 105 240 90 255 90 263 104 285 105 270 120 285 135 240 165 240 180 270 195 240 210 180 210 165 195
Polygon -7500403 true true 135 195 135 240 120 255 105 255 105 285 135 285 165 240 165 195

line
true
0
Line -7500403 true 150 0 150 300

line half
true
0
Line -7500403 true 150 0 150 150

pentagon
false
0
Polygon -7500403 true true 150 15 15 120 60 285 240 285 285 120

person
false
0
Circle -7500403 true true 110 5 80
Polygon -7500403 true true 105 90 120 195 90 285 105 300 135 300 150 225 165 300 195 300 210 285 180 195 195 90
Rectangle -7500403 true true 127 79 172 94
Polygon -7500403 true true 195 90 240 150 225 180 165 105
Polygon -7500403 true true 105 90 60 150 75 180 135 105

plant
false
0
Rectangle -7500403 true true 135 90 165 300
Polygon -7500403 true true 135 255 90 210 45 195 75 255 135 285
Polygon -7500403 true true 165 255 210 210 255 195 225 255 165 285
Polygon -7500403 true true 135 180 90 135 45 120 75 180 135 210
Polygon -7500403 true true 165 180 165 210 225 180 255 120 210 135
Polygon -7500403 true true 135 105 90 60 45 45 75 105 135 135
Polygon -7500403 true true 165 105 165 135 225 105 255 45 210 60
Polygon -7500403 true true 135 90 120 45 150 15 180 45 165 90

sheep
false
0
Rectangle -7500403 true true 151 225 180 285
Rectangle -7500403 true true 47 225 75 285
Rectangle -7500403 true true 15 75 210 225
Circle -7500403 true true 135 75 150
Circle -16777216 true false 165 76 116

square
false
0
Rectangle -7500403 true true 30 30 270 270

square 2
false
0
Rectangle -7500403 true true 30 30 270 270
Rectangle -16777216 true false 60 60 240 240

star
false
0
Polygon -7500403 true true 151 1 185 108 298 108 207 175 242 282 151 216 59 282 94 175 3 108 116 108

target
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240
Circle -7500403 true true 60 60 180
Circle -16777216 true false 90 90 120
Circle -7500403 true true 120 120 60

tree
false
0
Circle -7500403 true true 118 3 94
Rectangle -6459832 true false 120 195 180 300
Circle -7500403 true true 65 21 108
Circle -7500403 true true 116 41 127
Circle -7500403 true true 45 90 120
Circle -7500403 true true 104 74 152

triangle
false
0
Polygon -7500403 true true 150 30 15 255 285 255

triangle 2
false
0
Polygon -7500403 true true 150 30 15 255 285 255
Polygon -16777216 true false 151 99 225 223 75 224

truck
false
0
Rectangle -7500403 true true 4 45 195 187
Polygon -7500403 true true 296 193 296 150 259 134 244 104 208 104 207 194
Rectangle -1 true false 195 60 195 105
Polygon -16777216 true false 238 112 252 141 219 141 218 112
Circle -16777216 true false 234 174 42
Rectangle -7500403 true true 181 185 214 194
Circle -16777216 true false 144 174 42
Circle -16777216 true false 24 174 42
Circle -7500403 false true 24 174 42
Circle -7500403 false true 144 174 42
Circle -7500403 false true 234 174 42

turtle
true
0
Polygon -10899396 true false 215 204 240 233 246 254 228 266 215 252 193 210
Polygon -10899396 true false 195 90 225 75 245 75 260 89 269 108 261 124 240 105 225 105 210 105
Polygon -10899396 true false 105 90 75 75 55 75 40 89 31 108 39 124 60 105 75 105 90 105
Polygon -10899396 true false 132 85 134 64 107 51 108 17 150 2 192 18 192 52 169 65 172 87
Polygon -10899396 true false 85 204 60 233 54 254 72 266 85 252 107 210
Polygon -7500403 true true 119 75 179 75 209 101 224 135 220 225 175 261 128 261 81 224 74 135 88 99

wheel
false
0
Circle -7500403 true true 3 3 294
Circle -16777216 true false 30 30 240
Line -7500403 true 150 285 150 15
Line -7500403 true 15 150 285 150
Circle -7500403 true true 120 120 60
Line -7500403 true 216 40 79 269
Line -7500403 true 40 84 269 221
Line -7500403 true 40 216 269 79
Line -7500403 true 84 40 221 269

x
false
0
Polygon -7500403 true true 270 75 225 30 30 225 75 270
Polygon -7500403 true true 30 75 75 30 270 225 225 270

@#$#@#$#@
NetLogo 4.0.5
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
default
0.0
-0.2 0 1.0 0.0
0.0 1 1.0 0.0
0.2 0 1.0 0.0
link direction
true
0
Line -7500403 true 150 150 90 180
Line -7500403 true 150 150 210 180

@#$#@#$#@
