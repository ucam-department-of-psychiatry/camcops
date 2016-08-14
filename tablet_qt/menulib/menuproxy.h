#pragma once
#include <type_traits>  // for std::is_base_of
#include <QSharedPointer>

// see taskfactory.h

class CamcopsApp;
class MenuWindow;


// ============================================================================
// MenuProxy<T>: encapsulates MenuWindow-derived classes, for MenuItem
// instances that say "go to another menu".
// ============================================================================

class MenuProxyBase
{
public:
    MenuProxyBase() {}
    virtual ~MenuProxyBase() {}
    virtual MenuWindow* create(CamcopsApp& app) = 0;
};


template<class Derived> class MenuProxy : public MenuProxyBase
{
    static_assert(std::is_base_of<MenuWindow, Derived>::value,
                  "You can only use MenuWindow-derived classes here");
public:
    MenuProxy() {}
    virtual MenuWindow* create(CamcopsApp& app) override
    {
        return new Derived(app);
    }
};


typedef QSharedPointer<MenuProxyBase> MenuProxyPtr;
