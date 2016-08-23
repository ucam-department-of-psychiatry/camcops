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
    // Absence of virtual destructor here can lead to a crash,
    // even if Base has a virtual destructor? I'm not sure - either that,
    // or it was a QMediaPlayer destructor problem.
    virtual ~Cloneable()
    {}
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
    // (Absence of virtual destructor here can lead to a crash, presumably,
    // as above.)
    virtual ~MutilevelCloneable()
    {}
};
