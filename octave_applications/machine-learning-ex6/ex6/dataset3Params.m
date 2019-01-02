function [C, sigma] = dataset3Params(X, y, Xval, yval)
%DATASET3PARAMS returns your choice of C and sigma for Part 3 of the exercise
%where you select the optimal (C, sigma) learning parameters to use for SVM
%with RBF kernel
%   [C, sigma] = DATASET3PARAMS(X, y, Xval, yval) returns your choice of C and 
%   sigma. You should complete this function to return the optimal C and 
%   sigma based on a cross-validation set.
%

% You need to return the following variables correctly.
C = 0.1;
sigma = 0.1;

% ====================== YOUR CODE HERE ======================
% Instructions: Fill in this function to return the optimal C and sigma
%               learning parameters found using the cross validation set.
%               You can use svmPredict to predict the labels on the cross
%               validation set. For example, 
%                   predictions = svmPredict(model, Xval);
%               will return the predictions on the cross validation set.
%
%  Note: You can compute the prediction error using 
%        mean(double(predictions ~= yval))
%

sigma_curr = sigma;
err_best = 1000;

while (sigma_curr<0.2)
  C_curr = 0.1;
  while (C_curr<1)
    model= svmTrain(X, y, C_curr, @(x1, x2) gaussianKernel(x1, x2, sigma_curr)); 
    predictions = svmPredict(model, Xval);
    C_curr
    sigma_curr
    err_best
    err = mean(double(predictions ~= yval))
    if (err < err_best)
      err_best = err;
      C = C_curr ;
      sigma = sigma_curr ;
    endif
    C_curr = C_curr+0.1;
  end
  sigma_curr = sigma_curr+0.1;
end


C
sigma



% =========================================================================

end