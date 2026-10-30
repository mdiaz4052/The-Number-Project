
#lang racket

(define maxwell-1d
  (hash
   'name "maxwell-1d"
   'coordinates (list `x)
   'state (list `Ex `Ey `Ez `Bx `By `Bz)
   'state-assumptions (list)
   'parameters (list `c)
   'parameters-assumptions (list `(> c 0.0))
   'fluxes (list
            (list 0.0
                  `(* (* c c) Bz)
                  `(- (* (* c c) By))
                  0.0
                  `(- Ez)
                  `Ey))
   'wavespeeds (list
                (list `(- c)
                      `(- c)
                      `c
                      `c
                      0.0
                      0.0))
   'diffusive-fluxes (list
                      (list 0.0 0.0 0.0 0.0 0.0 0.0))
   )
  )

(define lax-friedrichs-1d
  (hash
   'name "lax-friedrichs"
   'waves (list
           (let ([flux_Ex_L 0.0]
                 [flux_Ex_R 0.0]
                 [flux_Ey_L `(* (* c c) Bz_L)]
                 [flux_Ey_R `(* (* c c) Bz_R)]
                 [flux_Ez_L `(- (* (* c c) By_L))]
                 [flux_Ez_R `(- (* (* c c) By_R))]
                 [flux_Bx_L 0.0]
                 [flux_Bx_R 0.0]
                 [flux_By_L `(- Ez_L)]
                 [flux_By_R `(- Ez_R)]
                 [flux_Bz_L `Ey_L]
                 [flux_Bz_R `Ey_R]
                 [amax `(abs c)])
             (list
              (list `(* 0.5 (- (- Ex_R Ex_L) (/ (- ,flux_Ex_R ,flux_Ex_L) ,amax)))
                    `(* 0.5 (- (- Ey_R Ey_L) (/ (- ,flux_Ey_R ,flux_Ey_L) ,amax)))
                    `(* 0.5 (- (- Ez_R Ez_L) (/ (- ,flux_Ez_R ,flux_Ez_L) ,amax)))
                    `(* 0.5 (- (- Bx_R Bx_L) (/ (- ,flux_Bx_R ,flux_Bx_L) ,amax)))
                    `(* 0.5 (- (- By_R By_L) (/ (- ,flux_By_R ,flux_By_L) ,amax)))
                    `(* 0.5 (- (- Bz_R Bz_L) (/ (- ,flux_Bz_R ,flux_Bz_L) ,amax))))
              (list `(* 0.5 (+ (- Ex_R Ex_L) (/ (- ,flux_Ex_R ,flux_Ex_L) ,amax)))
                    `(* 0.5 (+ (- Ey_R Ey_L) (/ (- ,flux_Ey_R ,flux_Ey_L) ,amax)))
                    `(* 0.5 (+ (- Ez_R Ez_L) (/ (- ,flux_Ez_R ,flux_Ez_L) ,amax)))
                    `(* 0.5 (+ (- Bx_R Bx_L) (/ (- ,flux_Bx_R ,flux_Bx_L) ,amax)))
                    `(* 0.5 (+ (- By_R By_L) (/ (- ,flux_By_R ,flux_By_L) ,amax)))
                    `(* 0.5 (+ (- Bz_R Bz_L) (/ (- ,flux_Bz_R ,flux_Bz_L) ,amax))))
              )
             )
           )
   'speeds (list
            (let ([amax `(abs c)])
              (list `(- ,amax) amax)))
   )
  )

(define minmod-1d
  (hash
   'name "minmod"
   'order 2
   'left-reconstruction (list
                         (let ([minmod_Ex `(+ (max 0.0 (min (- Ex Ex_L) (- Ex_R Ex))) (min 0.0 (max (- Ex Ex_L) (- Ex_R Ex))))]
                               [minmod_Ey `(+ (max 0.0 (min (- Ey Ey_L) (- Ey_R Ey))) (min 0.0 (max (- Ey Ey_L) (- Ey_R Ey))))]
                               [minmod_Ez `(+ (max 0.0 (min (- Ez Ez_L) (- Ez_R Ez))) (min 0.0 (max (- Ez Ez_L) (- Ez_R Ez))))]
                               [minmod_Bx `(+ (max 0.0 (min (- Bx Bx_L) (- Bx_R Bx))) (min 0.0 (max (- Bx Bx_L) (- Bx_R Bx))))]
                               [minmod_By `(+ (max 0.0 (min (- By By_L) (- By_R By))) (min 0.0 (max (- By By_L) (- By_R By))))]
                               [minmod_Bz `(+ (max 0.0 (min (- Bz Bz_L) (- Bz_R Bz))) (min 0.0 (max (- Bz Bz_L) (- Bz_R Bz))))])
                           (list `(- Ex (* 0.5 ,minmod_Ex))
                                 `(- Ey (* 0.5 ,minmod_Ey))
                                 `(- Ez (* 0.5 ,minmod_Ez))
                                 `(- Bx (* 0.5 ,minmod_Bx))
                                 `(- By (* 0.5 ,minmod_By))
                                 `(- Bz (* 0.5 ,minmod_Bz)))))
   'right-reconstruction (list
                          (let ([minmod_Ex `(+ (max 0.0 (min (- Ex Ex_L) (- Ex_R Ex))) (min 0.0 (max (- Ex Ex_L) (- Ex_R Ex))))]
                                [minmod_Ey `(+ (max 0.0 (min (- Ey Ey_L) (- Ey_R Ey))) (min 0.0 (max (- Ey Ey_L) (- Ey_R Ey))))]
                                [minmod_Ez `(+ (max 0.0 (min (- Ez Ez_L) (- Ez_R Ez))) (min 0.0 (max (- Ez Ez_L) (- Ez_R Ez))))]
                                [minmod_Bx `(+ (max 0.0 (min (- Bx Bx_L) (- Bx_R Bx))) (min 0.0 (max (- Bx Bx_L) (- Bx_R Bx))))]
                                [minmod_By `(+ (max 0.0 (min (- By By_L) (- By_R By))) (min 0.0 (max (- By By_L) (- By_R By))))]
                                [minmod_Bz `(+ (max 0.0 (min (- Bz Bz_L) (- Bz_R Bz))) (min 0.0 (max (- Bz Bz_L) (- Bz_R Bz))))])
                            (list `(+ Ex (* 0.5 ,minmod_Ex))
                                  `(+ Ey (* 0.5 ,minmod_Ey))
                                  `(+ Ez (* 0.5 ,minmod_Ez))
                                  `(+ Bx (* 0.5 ,minmod_Bx))
                                  `(+ By (* 0.5 ,minmod_By))
                                  `(+ Bz (* 0.5 ,minmod_Bz)))))
   )
  )
            