#pragma once


namespace Numeric {

    int numDigitsInteger(int number, bool count_sign = false);
    int firstDigitsInteger(int number, int n_digits);
    int numDigitsDouble(double number, int max_dp = 50);
    double firstDigitsDouble(double number, int n_digits, int max_dp = 50);

}
