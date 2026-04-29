package duui.monitoring.weaving;

import duui.monitoring.model.DUUIDispatchMode;
import duui.monitoring.model.DUUIStatus;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Phase {
    DUUIStatus status();

    DUUIDispatchMode dispatch();
}
