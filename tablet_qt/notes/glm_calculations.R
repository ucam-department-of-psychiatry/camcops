library(mlmRev)

irls <- function(A, b, family=binomial, maxit=25, tol=1e-08)
{
    x = rep(0,ncol(A))
    for(j in 1:maxit)
    {
        eta    = A %*% x
        g      = family()$linkinv(eta)
        gprime = family()$mu.eta(eta)
        z      = eta + (b - g) / gprime
        W      = as.vector(gprime^2 / family()$variance(g))
        xold   = x
        x      = solve(crossprod(A,W*A), crossprod(A,W*z), tol=2*.Machine$double.eps)
        if(sqrt(crossprod(x-xold)) < tol) break
    }
    cat("eta:\n")
    print(eta)
    list(
        coefficients=x,
        iterations=j,
        # Debugging:
        last_eta=eta,
        last_g=g,
        last_gprime=gprime,
        last_z = z,
        last_W = W
    )
}


d <- data.frame(
    x = c(0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50, 4.00, 4.25, 4.50, 4.75, 5.00, 5.50),
    y = c(0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1)
)

data("Contraception",package="mlmRev")

# Model estimated with R's glm function, returning model matrix and response
# in $x and $y, respectively:
R_GLM = glm(formula = use ~ age + I(age^2) + urban + livch,
            family = binomial, x=TRUE, data=Contraception)

# Model estimated with our radically stripped-down minimalist implementation:
mini = irls(R_GLM$x, R_GLM$y, family=binomial)

print(data.frame(R_GLM=coef(R_GLM), minimalist=coef(mini)))


# r_glm <- glm(y ~ x, family=binomial(link='logit'), data=d)
# mini_model <- irls(matrix(d$x, ncol=1), matrix(d$y, ncol=1), family=binomial)
