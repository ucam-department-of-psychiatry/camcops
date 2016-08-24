#include <QDebug>
#include "lib/uifunc.h"
#include "questionnairefunc.h"


void QuestionnaireFunc::ensureValidNvpList(const NameValuePairList& options)
{
    QList<QVariant> values;
    for (const NameValuePair& nvp : options) {
        if (values.contains(nvp.value())) {
            qCritical() << "Name/value pair contains duplicate value:"
                        << nvp.value();
            UiFunc::stopApp("Duplicate name/value pair for name: " +
                            nvp.name());
        }
    }
}
