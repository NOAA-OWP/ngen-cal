from math import log

def dds(start_iteration: int, iterations: int, calibration_object: Calibratable, meta: CalibrationMeta):
    """
        Functional form of the dds loop
    """
    if iterations < 2:
        raise(ValueError("iterations must be >= 2"))
    if start_iteration > iterations:
        raise(ValueError("start_iteration must be <= iterations"))
    for i in range(start_iteration, iterations+1):
        #Calculate probability of inclusion
        inclusion_probability = 1 - log(i)/log(iterations)
        print( "inclusion probability: {}".format(inclusion_probability) )
        #select a random subset of variables to modify
        #TODO convince myself that grabbing a random selction of P fraction of items
        #is the same as selecting item with probability P
        neighborhood = calibration_object.variables.sample(frac=inclusion_probability)
        if neighborhood.empty:
           neighborhood = calibration_object.variables.sample(n=1)
        print( "neighborhood: {}".format(neighborhood) )
        #Copy the best parameter values so far into the next iterations parameter list
        calibration_object.df[i] = calibration_object.df[best_params]
        #print( data.calibration_df )
        for n in neighborhood:
            #permute the variables in neighborhood
            #using a random normal sample * sigma, sigma = 0.2*(max-min)
            #print(n, best_params)
            new = calibration_object.df.loc[n, best_params] + calibration_object.df.loc[n, 'sigma']*pd.np.random.normal(0,1)
            lower =  calibration_object.df.loc[n, 'lower']
            upper = calibration_object.df.loc[n, 'upper']
            #print( new )
            #print( lower )
            #print( upper )
            if new < lower:
                new = lower + (lower - new)
                if new > upper:
                    new = lower
            elif new > upper:
                new = upper - (new - upper)
                if new < lower:
                    new = upper
            calibration_object.df.loc[n, i] = new
        """
            At this point, we need to re-run cmd with the new parameters assigned correctly and evaluate the objective function
        """
        calibration_object.update_state(i)
        #Run cmd Again...
        print("Running {} for iteration {}".format(cmd, i))
        subprocess.check_call(meta.cmd, stdout=meta.log_file, shell=True)
        #read output and calculate objective_func
        score =  objective_func(hydrograph_output_file, observed_df, evaluation_range)
        shutil.move(hydrograph_output_file, '{}_{}'.format(hydrograph_output_file, i))
        if score <= best_score:
            best_params = i
            best_score = score
            #Score has improved, run next simulation with
        print("Current score {}\nBest score {}".format(score, best_score))
        calibration_object.checkpoint( config.workdir )
        write_param_log_file(i, best_params, best_score)
        write_objective_log_file(i, score)
        print("Best parameters at column {} in calibration_df_state.msg".format(best_params))
