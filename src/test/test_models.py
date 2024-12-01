test_model = {
    "temperature": {
        "tags": {
            "plant": 100,
            "line": 5,
            "sensor_id": "id"
        },
        "metrics": {
            "temperature": {
                "key": {
                    "value": "value"
                },
                "type": {
                    "value": "FLOAT"
                },
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
                "mode": {
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
                }
            },
            "button": {
                "key": {
                    "value": "button_press"
                },
                "type": {
                    "value": "BOOL"
                },
                "true_ratio": {
                    "value": 0.001
                }
            }
        }
    }
}
test_model2 = {
    "booleans": {
        "tags": {
            "plant": 100,
            "line": 5,
            "sensor_id": "id"
        },
        "metrics": {
            "switch": {
                "key": {
                    "value": "switch_on"
                },
                "type": {
                    "value": "BOOL"
                },
                "true_ratio": {
                    "value": 0.9
                }
            },
            "button": {
                "key": {
                    "value": "button_press"
                },
                "type": {
                    "value": "BOOL"
                },
                "true_ratio": {
                    "value": 0.001
                }
            }
        }
    }
}
metrics_model_float1_bool1 = {
    "temperature": {
        "key": {
            "value": "value"
        },
        "type": {
            "value": "FLOAT"
        },
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
        }
    },
    "button": {
        "key": {
            "value": "button_press"
        },
        "type": {
            "value": "BOOL"
        },
        "true_ratio": {
            "value": 0.01
        }
    }
}
metrics_model_string = {
    "string": {
        "key": {
            "value": "not_implemented_sensor_type"
        },
        "type": {
            "value": "STRING"
        },
        "true_ratio": {
            "value": "not_implemented"
        }
    }
}
tag_model_plant100_line5_sensorId = {
    "plant": 100,
    "line": 5,
    "sensor_id": "id"
}
float_model = {
    "key": {
        "value": "test"
    },
    "type": {
        "value": "FLOAT"
    },
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
        "value": 0.001,
    },
    "error_length": {
        "value": 1.08,
    }
}
bool_model = {
    "key": {
        "value": "button_press"
    },
    "type": {
        "value": "BOOL"
    },
    "true_ratio": {
        "value": 0.001
    }
}
