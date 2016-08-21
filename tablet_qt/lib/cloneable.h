#pragma once
#include <QSharedPointer>


template <typename Base, typename Derived>
class Cloneable : virtual public Base
{
public:
    virtual QSharedPointer<Base> clone() const override
    {
        return QSharedPointer<Base>(
            new Derived(static_cast<Derived const &>(*this))
        );
    }
};


// For multilevel inheritance, because you do not get automatic conversion
// of the QSharedPointer:
template <typename UltimateBase, typename ImmediateBase, typename Derived>
class MutilevelCloneable : virtual public ImmediateBase
{
public:
    virtual QSharedPointer<UltimateBase> clone() const override
    {
        return QSharedPointer<UltimateBase>(
            new Derived(static_cast<Derived const &>(*this))
        );
    }
};
