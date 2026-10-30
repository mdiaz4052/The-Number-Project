
#lang racket

(define inviscid-burgers-1d
  (hash
   'name "inviscid-burgers-1d"
   'coordinates (list `x)
   'state (list `f)
   'state-assumptions (list)
   'parameters (list)
   'parameters-assumptions (list)
   'fluxes (list
            (list `(* 0.5 f f)))
   'wavespeeds (list
                (list `f))
   'diffusive-fluxes (list
                      (list 0.0))
   )
  )

(define lax-friedrichs-1d
  (hash
   'name "lax-friedrichs"
   'waves (list
           (let ([flux_f_L `(* 0.5 (* f_L f_L))]
                 [flux_f_R `(* 0.5 (* f_R f_R))]
                 [amax `(max (abs f_L) (abs f_R))])
             (list
              (list `(* 0.5 (- (- f_R f_L) (/ (- ,flux_f_R ,flux_f_L) ,amax))))
              (list `(* 0.5 (+ (- f_R f_L) (/ (- ,flux_f_R ,flux_f_L) ,amax))))
              )
             )
           )
   'speeds (list
            (let ([amax `(max (abs f_L) (abs f_R))])
              (list `(- ,amax) amax)))
   )
  )

(define minmod-1d
  (hash
   'name "minmod"
   'order 2
   'left-reconstruction (list
                         (let ([minmod_f `(+ (max 0.0 (min (- f f_L) (- f_R f))) (min 0.0 (max (- f f_L) (- f_R f))))])
                           (list `(- f (* 0.5 ,minmod_f)))))
   'right-reconstruction (list
                          (let ([minmod_f `(+ (max 0.0 (min (- f f_L) (- f_R f))) (min 0.0 (max (- f f_L) (- f_R f))))])
                            (list `(+ f (* 0.5 ,minmod_f)))))
   )
  )
            