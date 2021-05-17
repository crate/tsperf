test_model = {
    "description": "test",
    "temperature": {
        "tags": {"description": "test", "plant": 100, "line": 5, "sensor_id": "id"},
        "metrics": {
            "description": "test",
            "temperature": {
                "description": "test",
                "key": {"description": "test", "value": "value"},
                "type": {"description": "test", "value": "FLOAT"},
                "min": {
                    "description": "test",
                    "value": 6.0,
                },
                "max": {
                    "description": "test",
                    "value": 7.4,
                },
                "mean": {
                    "description": "test",
                    "value": 6.4,
                },
                "median": {
                    "description": "test",
                    "value": 6.3,
                },
                "mode": {
                    "description": "test",
                    "value": 6.3,
                },
                "stdev": {
                    "description": "test",
                    "value": 0.2,
                },
                "variance": {
                    "description": "test",
                    "value": 0.03,
                },
                "error_rate": {
                    "description": "test",
                    "value": 0.005,
                },
                "error_length": {
                    "description": "test",
                    "value": 1.08,
                },
            },
            "button": {
                "description": "test",
                "key": {"description": "test", "value": "button_press"},
                "type": {"description": "test", "value": "BOOL"},
                "true_ratio": {"description": "test", "value": 0.001},
            },
        },
    },
}

test_model2 = {
    "booleans": {
        "description": "test",
        "tags": {"description": "test", "plant": 100, "line": 5, "sensor_id": "id"},
        "metrics": {
            "description": "test",
            "switch": {
                "description": "test",
                "key": {"description": "test", "value": "switch_on"},
                "type": {"description": "test", "value": "BOOL"},
                "true_ratio": {"description": "test", "value": 0.9},
            },
            "button": {
                "description": "test",
                "key": {"description": "test", "value": "button_press"},
                "type": {"description": "test", "value": "BOOL"},
                "true_ratio": {"description": "test", "value": 0.001},
            },
        },
    }
}

test_model3 = {
    "booleans": {
        "description": "test",
        "tags": {
            "description": "test",
            "plant": ["A", "B", "C", "D", "E"],
            "line": ["L1", "L2", "L3"],
            "sensor_id": "id",
        },
        "metrics": {
            "description": "test",
            "switch": {
                "description": "test",
                "key": {"description": "test", "value": "switch_on"},
                "type": {"description": "test", "value": "BOOL"},
                "true_ratio": {"description": "test", "value": 0.9},
            },
            "button": {
                "description": "test",
                "key": {"description": "test", "value": "button_press"},
                "type": {"description": "test", "value": "BOOL"},
                "true_ratio": {"description": "test", "value": 0.001},
            },
        },
    }
}

metrics_model_float1_bool1 = {
    "temperature": {
        "key": {"value": "value"},
        "type": {"value": "FLOAT"},
        "min": {
            "value": 6.0,
        },
        "max": {
            "value": 7.4,
        },
        "mean": {
            "value": 6.4,
        },
        "median": {
            "value": 6.3,
        },
        "stdev": {
            "value": 0.2,
        },
        "variance": {
            "value": 0.03,
        },
        "error_rate": {
            "value": 0.005,
        },
        "error_length": {
            "value": 1.08,
        },
    },
    "button": {
        "key": {"value": "button_press"},
        "type": {"value": "BOOL"},
        "true_ratio": {"value": 0.01},
    },
}
metrics_model_string = {
    "string": {
        "key": {"value": "not_implemented_sensor_type"},
        "type": {"value": "STRING"},
        "true_ratio": {"value": "not_implemented"},
    }
}
tag_model_plant100_line5_sensorId = {"plant": 100, "line": 5, "sensor_id": "id"}

tag_model_list = {
    "plant": ["A", "B", "C", "D", "E"],
    "line": ["L1", "L2", "L3"],
    "sensor_id": "id",
}

bool_model = {
    "key": {"value": "button_press"},
    "type": {"value": "BOOL"},
    "true_ratio": {"value": 0.001},
}
