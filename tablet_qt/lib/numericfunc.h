#pragma once


namespace Numeric {

    // For integer validation
    int numDigitsInteger(int number, bool count_sign = false);
    int firstDigitsInteger(int number, int n_digits);
    bool isValidStartToInteger(int number, int bottom, int top);
    bool extendedIntegerMustExceedTop(int number, int bottom, int top);
    bool extendedIntegerMustBeLessThanBottom(int number, int bottom, int top);

    // For double validation:
    int numDigitsDouble(double number, int max_dp = 50);
    double firstDigitsDouble(double number, int n_digits, int max_dp = 50);
    bool isValidStartToDouble(double number, double bottom, double top);
    bool extendedDoubleMustExceed(double number, double bottom, double top);
    bool extendedDoubleMustBeLessThan(double number, double bottom, double top);
}
