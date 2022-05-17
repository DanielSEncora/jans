package io.jans.configapi.core.util;

import io.jans.as.model.json.JsonApplier;
import io.jans.orm.exception.MappingException;
import io.jans.orm.reflect.property.Getter;
import io.jans.orm.reflect.property.Setter;
import io.jans.orm.reflect.util.ReflectHelper;

import jakarta.enterprise.context.ApplicationScoped;
import java.beans.Introspector;
import java.beans.IntrospectionException;
import java.beans.PropertyDescriptor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@ApplicationScoped
public class DataUtil {

    private DataUtil() {
    }

    private static final Logger logger = LoggerFactory.getLogger(DataUtil.class);

    public static Class<?> getPropertType(String className, String name) throws MappingException {
        logger.error("className:{} , name:{} ", className, name);
        return ReflectHelper.reflectedPropertyClass(className, name);

    }

    public static Getter getGetterMethod(Class<?> clazz, String name) throws MappingException {
        logger.error("Get Getter fromclazz:{} , name:{} ", clazz, name);
        return ReflectHelper.getGetter(clazz, name);
    }

    public static Setter getSetterMethod(Class<?> clazz, String name) throws MappingException {
        logger.error("Get Setter from clazz:{} for name:{} ", clazz, name);
        return ReflectHelper.getSetter(clazz, name);
    }

    public static Object getValue(Object object, String property) throws MappingException {
        logger.error("Get value from object:{} for property:{} ", object, property);
        return ReflectHelper.getValue(object, property);
    }

    public static Method getSetter(String fieldName, Class clazz) throws Exception {
        PropertyDescriptor[] props = Introspector.getBeanInfo(clazz).getPropertyDescriptors();
        for (PropertyDescriptor p : props)
            if (p.getName().equals(fieldName))
                return p.getWriteMethod();
        return null;
    }

    public Object invokeReflectionGetter(Object obj, String variableName) {
        try {
            PropertyDescriptor pd = new PropertyDescriptor(variableName, obj.getClass());
            Method getter = pd.getReadMethod();
            if (getter != null) {
                return getter.invoke(obj);
            } else {
                logger.error(String.format("Getter Method not found for class: %s property: %s",
                        obj.getClass().getName(), variableName));
            }
        } catch (IllegalAccessException | IllegalArgumentException | InvocationTargetException
                | IntrospectionException e) {
            logger.error(String.format("Getter Method ERROR for class: %s property: %s", obj.getClass().getName(),
                    variableName), e);
        }
        return null;
    }

    public static void invokeReflectionSetter(Object obj, String propertyName, Object variableValue) {
        PropertyDescriptor pd;
        try {
            pd = new PropertyDescriptor(propertyName, obj.getClass());
            Method method = pd.getWriteMethod();
            if (method != null) {
                method.invoke(obj, variableValue);
            } else {
                logger.error(String.format(" Setter Method not found for class: %s property: %s",
                        obj.getClass().getName(), propertyName));
            }
        } catch (IntrospectionException | IllegalAccessException | IllegalArgumentException
                | InvocationTargetException e) {
            logger.error(String.format("\n\n Setter Method invocation ERROR for class: %s property: %s",
                    obj.getClass().getName(), propertyName), e);
        }
    }

    public static boolean containsField(List<Field> allFields, String attribute) {
        logger.error("allFields:{},  attribute:{}, allFields.contains(attribute):{} ", allFields, attribute,
                allFields.stream().anyMatch(f -> f.getName().equals(attribute)));

        return allFields.stream().anyMatch(f -> f.getName().equals(attribute));
    }

    public static List<Field> getAllFields(Class<?> type) {
        List<Field> allFields = new ArrayList<>();
        allFields = getAllFields(allFields, type);
        logger.error("Fields:{} of type:{}  ", allFields, type);

        return allFields;
    }

    public static List<Field> getAllFields(List<Field> fields, Class<?> type) {
        logger.error("Getting fields type:{} - fields:{} ", type, fields);
        fields.addAll(Arrays.asList(type.getDeclaredFields()));

        if (type.getSuperclass() != null) {
            getAllFields(fields, type.getSuperclass());
        }
        logger.error("Final fields:{} of type:{} ", fields, type);
        return fields;
    }

    public static Map<String, String> getFieldTypeMap(Class<?> clazz) {
        logger.error("clazz:{} ", clazz);
        Map<String, String> propertyTypeMap = new HashMap<>();

        if (clazz == null) {
            return propertyTypeMap;
        }

        List<Field> fields = getAllFields(clazz);
        logger.error("fields:{} ", fields);

        for (Field field : fields) {
            logger.error(
                    "field:{} , field.getAnnotatedType():{}, field.getAnnotations():{} , field.getType().getAnnotations():{}, field.getType().getCanonicalName():{} , field.getType().getClass():{} , field.getType().getClasses():{} , field.getType().getComponentType():{}",
                    field, field.getAnnotatedType(), field.getAnnotations(), field.getType().getAnnotations(),
                    field.getType().getCanonicalName(), field.getType().getClass(), field.getType().getClasses(),
                    field.getType().getComponentType());
            propertyTypeMap.put(field.getName(), field.getType().getSimpleName());
        }
        logger.error("Final propertyTypeMap{} ", propertyTypeMap);
        return propertyTypeMap;
    }

    public static Map<Field, Class> getPropertyTypeMap(Class<?> clazz) {
        logger.error("clazz:{} for getting property and field map ", clazz);
        Map<Field, Class> propertyTypeMap = new HashMap<>();
        if (clazz == null) {
            return propertyTypeMap;
        }
        logger.error("clazz.getCanonicalName():{}, clazz.getName():{}, clazz.getPackageName():{} ",
                clazz.getCanonicalName(), clazz.getName(), clazz.getPackageName());
        String className = clazz.getName();
        List<Field> fields = getAllFields(clazz);
        logger.error("fields:{} ", fields);
        if (fields == null) {
            return propertyTypeMap;
        }
        for (Field field : fields) {
            logger.error("field:{} ", field);
            Class dataTypeClass = getPropertType(className, field.getName());
            logger.error("dataTypeClass:{} ", dataTypeClass);
            propertyTypeMap.put(field, dataTypeClass);
        }

        logger.error("Final propertyTypeMap{} ", propertyTypeMap);
        return propertyTypeMap;
    }

    public static Object invokeGetterMethod(Object obj, String variableName) {
        return JsonApplier.getInstance().invokeReflectionGetter(obj, variableName);
    }

}
